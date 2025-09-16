# Intro

आज हम इस **`qr_code_generator`** Go प्रोजेक्ट को step-by-step समझेंगे — बिलकुल वैसे जैसे आप एक technical YouTube वीडियो में सुनते। मैं explanations हिंदी (देवनागरी) में दूँगा लेकिन जो भी technical term है वो English में रखूँगा — ताकि interview / code-reading दोनों के लिए सही रहे।
हम पहले architecture देखेंगे, फिर हर फ़ाइल का purpose और उसके important code-blocks **line-by-line (block-wise)** समझाएँगे — साथ में design decisions और improvements भी बताऊँगा।

---

# High-level architecture (फोल्डर / फ़ाइलों का breakdown)

यह प्रोजेक्ट Clean-ish separation अपनाता है (fully formal clean-arch नहीं, पर separation of concerns अच्छे से दिखता है):

* `cmd/main.go` — CLI entrypoint. Commands parse करता है: `generate`, `custom`, `batch`, `scan`, `cache`.
* `internal/` — core logic:

  * `internal/generator/` — QR generators (`standard.go`, `custom.go`, `batch.go`)
  * `internal/factory/` — Factory method to choose generator
  * `internal/cache/` — in-memory thread-safe cache
  * `internal/db/` — DB init (GORM)
  * `internal/models/` — GORM model(s)
  * `internal/scanner/` — reads & decodes image QR using tuotoo/qrcode
* `README.md` — project summary (note: README कहता Postgres पर GORM है पर code MySQL driver use कर रहा — mismatch, नीचे बताऊँगा)

Design patterns & concepts used:

* **Factory Method** — `factory.QRFactory` देता है generator abstraction।
* **Interface / Inversion of Control** — `QRGenerator` interface से concrete generators decoupled हैं।
* **Concurrency** — `BatchQRGenerator` goroutines और `sync.WaitGroup` use करता है।
* **Thread-safe cache** — custom map + `sync.RWMutex`।
* **Persistence** — GORM (DB connection globally exposed as `db.DB`) और AutoMigrate।

---

# File-by-file walkthrough

> नीचे हर फ़ाइल में मैं पहले `What/Why/UsedBy` बताऊँगा, फिर code blocks को spoken-style में explain करूँगा — important lines पर ध्यान देंगे और जहाँ improvements चाहिए वहाँ मैंने **Tip / Gotcha** भी add किया है.

---

## `README.md`

**What it does:** Project summary — बताता कि generator में Factory Method pattern, cache, GORM, standard/custom/batch and scanner हैं.
**Why:** Quick overview for repo visitors.
**Used by:** humans 😄 (devs), कोई runtime dependency नहीं.

**Notes / Gotchas**

* README में लिखा है **PostgreSQL integration**, लेकिन actual `internal/db/db.go` uses **MySQL driver** (`gorm.io/driver/mysql`). यह mismatch confuse करेगा — README या code दोनों में से किसी एक को sync करना चाहिए.

---

## `cmd/main.go`

**What:** CLI entrypoint. `main()` में command line arguments देखकर अलग operations चलाता है.
**Why folder:** `cmd/` CLI programs के लिए canonical place है.
**Used by:** Devs running `go run cmd/main.go ...` या compiled binary.

### Key lines — walkthrough (spoken style)

```go
db.InitDB()
```

* सबसे पहले DB initialize करते हैं। मतलब अगर DB credentials मिले हैं तो connection बन जाएगी और AutoMigrate चलेगा।
* **Architectural note:** global `db.DB` set हो जाता है, जिससे बाकी packages उस global var को use कर सकते हैं (convenient but global state — production में dependency injection बेहतर).

```go
if len(os.Args) < 2 {
    log.Fatal("Usage: go run cmd/main.go [generate|custom|batch|scan|cache] <data/file>")
}
command := os.Args[1]
```

* CLI parsing minimal है: first arg command, second arg data/file। Simple, but no proper flags/validation।

Switch cases:

* `generate`:

  ```go
  gen := factory.QRFactory("standard")
  file, err := gen.Generate(os.Args[2], nil)
  ```

  * Factory से `standard` generator लेते हैं और `Generate` चलाते हैं। `opts` nil है।
  * **Why factory?** ताकि main को concrete implementation की knowledge न हो — सिर्फ interface इस्तेमाल हो रहा है।

* `custom`:

  ```go
  gen := factory.QRFactory("custom")
  opts := map[string]string{}
  if len(os.Args) > 3 {
      opts["color"] = os.Args[3]
  }
  ```

  * third arg से color पास किया जा सकता है। Simple options map use किया गया — scalable नहीं है पर small usecases के लिए ठीक है।

* `batch`:

  * Uses `&generator.BatchQRGenerator{}` directly instead of factory; इधर factory भी batch return कर देता है पर main सीधे struct बना रहा है। थोड़ा inconsistency है — factory का use करना बेहतर रहता।

* `scan`:

  ```go
  content, err := scanner.Scan(os.Args[2])
  ```

  * file path pass करके scanner.Decode किया जाता है और result print होता है।

* `cache`:

  * `cache.GetFromCache(data)` call करके hit/miss दिखाते हैं।

**Improvements**

* CLI parsing के लिए `flag` या `cobra` उपयोग किया जा सकता है ताकि options साफ़ रहें।
* `QRFactory` का उपयोग consistent रखें (main में कहीं direct struct बनाना inconsistent है)।
* Arg validation और user-friendly errors add करें।

---

## `internal/cache/cache.go`

**What:** Thread-safe in-memory cache for `models.QRRecord`. Keys are SHA256 of the data string.
**Why:** Repeated QR generation/scans को cache कर के DB calls कम कर सकते हैं या duplicates identify कर सकते हैं.
**Used by:** `generator.StandardQRGenerator`, `generator.CustomQRGenerator`, `scanner.Scan` — सभी cache.AddToCache call करते हैं; और `cmd/main.go` cache query करता है।

### Walkthrough — important lines

```go
var mu sync.RWMutex
var qrCache = make(map[string]models.QRRecord)
```

* `mu` read-write mutex है जिससे concurrent goroutines safe तरीके से map access कर सकें। `qrCache` normal Go map है।
* **Why RWMutex?** read-heavy workloads में `RLock` multiple readers allow करता है, writers exclusive होते हैं।

```go
func hash(data string) string {
    h := sha256.Sum256([]byte(data))
    return hex.EncodeToString(h[:])
}
```

* Data को hash करके key बनाते हैं — इसका फायदा: keys का fixed length, और sensitive `data` map में plaintext में directly न रहे।
* **Alternative:** सीधे `data` भी key बन सकता था; hashing security/length benefit देता है पर collisions theoretically possible (sha256 negligible).

```go
func AddToCache(data string, record models.QRRecord) {
    mu.Lock()
    defer mu.Unlock()
    qrCache[hash(data)] = record
}

func GetFromCache(data string) (models.QRRecord, bool) {
    mu.RLock()
    defer mu.RUnlock()
    rec, found := qrCache[hash(data)]
    return rec, found
}
```

* Simple Add/Get with proper locking. Good.

**Improvements / Tips**

* अगर cache size बढ़ सकता है तो eviction (LRU) या TTL चाहिए — अभी unlimited growth होगा।
* Simpler alternative: `sync.Map` use कर के boilerplate कम किया जा सकता है, पर `sync.Map` semantics different होते हैं (read-heavy case में अच्छा)।
* Hashing step costs CPU for each lookup — weigh tradeoff.

---

## `internal/db/db.go`

**What:** Initialize GORM DB connection (code uses MySQL driver) and AutoMigrate `models.QRRecord`.
**Why:** Central place for DB setup.
**Used by:** `generator.*` and `scanner.*` use `db.DB` to create records.

### Walkthrough

```go
if err := godotenv.Load(); err != nil {
    log.Println("⚠️  No .env file found, falling back to system environment variables")
}
```

* `.env` optional है — local dev में helpful, otherwise environment vars used। Good.

```go
dsn := fmt.Sprintf("%s:%s@tcp(localhost:3306)/%s?charset=utf8mb4&parseTime=True&loc=Local",
    os.Getenv("DB_USER"), os.Getenv("DB_PASS"), os.Getenv("DB_NAME"))
DB, err = gorm.Open(mysql.Open(dsn), &gorm.Config{})
```

* **Important:** This explicitly uses **MySQL** (driver `mysql`) and hardcodes `localhost:3306`.
* **Mismatch:** README में PostgreSQL mention था — fix either README या code.

```go
if err := DB.AutoMigrate(&models.QRRecord{}); err != nil {
    log.Fatalf("❌ Failed to migrate schema: %v", err)
}
```

* AutoMigrate ensures table exists. Convenient for dev, but production में migrations careful तरीके से handle होने चाहिए।

**Improvements / Gotchas**

* Credentials logging: avoid printing secrets. Right now code doesn't print DSN but `godotenv` fallback message shows environment reliance. Make sure `.env` not committed.
* Expose DB connection pooling: `sqlDB, _ := DB.DB()` and set `SetMaxOpenConns`, `SetConnMaxLifetime` etc.
* Error handling: `log.Fatalf` kills program — ok for CLI app, but for libraries better return error.

---

## `internal/factory/generator_factory.go`

**What:** Factory Method implementation returning `QRGenerator` interface implementations.
**Why:** Decouples caller from concrete implementations.
**Used by:** `cmd/main.go`, possibly other callers.

### Walkthrough

```go
type QRGenerator interface {
    Generate(data string, opts map[string]string) (string, error)
}
```

* Interface defines contract — **Dependency Inversion**: callers code to interface, not implementation.

```go
func QRFactory(genType string) QRGenerator {
    switch genType {
    case "standard":
        return &generator.StandardQRGenerator{}
    case "custom":
        return &generator.CustomQRGenerator{}
    case "batch":
        return &generator.BatchQRGenerator{}
    default:
        panic("❌ Unsupported generator type")
    }
}
```

* **Behavior:** returns concrete instance based on genType.
* **Design note:** current implementation `panic` on unknown type — better return `(QRGenerator, error)` so callers can handle gracefully. `panic` is harsh for CLI tools (though acceptable if it's programmer error).

**Improvements**

* Return `(QRGenerator, error)` instead of panic.
* Consider registering generators dynamically or use enum/constants to avoid typos.

---

## `internal/generator/batch.go`

**What:** Reads a file (CSV or JSON) with a list of data strings and generates QR codes for each concurrently.
**Why:** Bulk QR creation support.
**Used by:** `cmd/main.go` (batch command).

### Walkthrough & issues

```go
var records []string

if opts != nil && opts["format"] == "csv" {
    file, err := os.Open(filePath)
    ...
    reader := csv.NewReader(file)
    lines, _ := reader.ReadAll()
    for _, line := range lines {
        if len(line) > 0 {
            records = append(records, line[0])
        }
    }
} else if opts != nil && opts["format"] == "json" {
    b, err := os.ReadFile(filePath)
    ...
    json.Unmarshal(b, &records)
} else {
    return "", fmt.Errorf("unsupported format")
}
```

* **CSV branch:** reads all lines and takes first column as data (`line[0]`).

  * **Bug/omission:** `reader.ReadAll()` error ignored (`lines, _ := ...`) — should check error.
* **JSON branch:** `json.Unmarshal` error not checked — critical omission.
* After parsing:

```go
var wg sync.WaitGroup
gen := &StandardQRGenerator{}
for _, rec := range records {
    wg.Add(1)
    go func(data string) {
        defer wg.Done()
        gen.Generate(data, nil)
    }(rec)
}
wg.Wait()
```

* **Concurrency:** For each record, a goroutine spawns calling Standard generator concurrently, with WaitGroup to wait for all to finish.
* **Important considerations:**

  * Errors from `gen.Generate` are ignored — you can't know if some writes failed.
  * Spawning unbounded goroutines for large files can exhaust resources (FDs, memory). Use a worker pool / semaphore (e.g., buffered channel) to limit concurrency.
  * Re-using `gen := &StandardQRGenerator{}` is fine as Standard generator has no per-call state; underlying operations (file write, cache, DB) are thread-safe (cache has mutex; GORM is safe for concurrent use usually). But confirm DB driver thread-safety.
  * If `records` is large, you may want to batch DB writes or rate-limit.

**Improvements**

* Validate and handle errors from `ReadAll` and `json.Unmarshal`.
* Return aggregate result or first error instead of silently ignoring.
* Limit concurrency with worker pool or `semaphore := make(chan struct{}, N)`.

---

## `internal/generator/custom.go`

**What:** Generates QR with customizable foreground/background colors and writes file. Also persists record to DB & cache.
**Why:** For colored/brandable QR codes.
**Used by:** `cmd/main.go` (custom command).

### Walkthrough (block-wise)

```go
if err := os.MkdirAll("output", os.ModePerm); err != nil { ... }
file := fmt.Sprintf("output/custom_qr_%d.png", time.Now().UnixNano())
qr, err := qrcode.New(data, qrcode.High)
```

* Ensure `output/` exists, build filename with timestamp (nanoseconds) to avoid collision, create `qrcode` with high error correction.

Default colors:

```go
fg := color.RGBA{0, 0, 0, 255}     // black
bg := color.RGBA{255, 255, 255, 255} // white
```

Parse options:

```go
if opts != nil {
    if c, ok := opts["color"]; ok && strings.TrimSpace(c) != "" {
        if parsed, perr := parseColor(strings.TrimSpace(c)); perr == nil {
            fg = parsed
        }
    }
    if c, ok := opts["bg"]; ok && strings.TrimSpace(c) != "" {
        if parsed, perr := parseColor(strings.TrimSpace(c)); perr == nil {
            bg = parsed
        }
    }
}
qr.ForegroundColor = fg
qr.BackgroundColor = bg
```

* `parseColor` supports named colors and hex strings. If parse fails, silently falls back to default — maybe better to return error to caller so they know color was invalid.

Write file & persist:

```go
if err := qr.WriteFile(256, file); err != nil { return "", err }

record := models.QRRecord{Data: data, Type: "custom", FilePath: file}
if db.DB != nil { db.DB.Create(&record) }
cache.AddToCache(data, record)
```

* Writes PNG; creates DB record and adds to cache.

### `parseColor` function

* Supports named colors: black, white, red, green, blue, yellow, purple, orange, gray/grey.
* Hex parsing:

  * Trim `#`. If 3-digit format, expands: `"0f8" -> "00ff88"` using `fmt.Sprintf("%c%c...", s[0], s[0], ...)`.
  * Then parses R,G,B pairs using `strconv.ParseUint(..., 16, 8)` and returns `color.RGBA`.

**Gotchas / Tips**

* The named colors include `"blue"` and `"green"` — if user had issue earlier with colors not working, the problem likely not in parseColor but maybe in CLI arg passing or the code not using `opts["color"]` properly. Ensure to pass color as third arg or via flags.
* `fmt.Sprintf("%c%c...")` approach works but could be a bit cryptic; another approach is `s = string([]byte{s[0], s[0], s[1], s[1], s[2], s[2]})` — both are fine.
* `parseColor` returns error if unsupported format — but caller ignores it (silently uses default). Consider returning error to user.

---

## `internal/generator/standard.go`

**What:** Basic QR generator—writes PNG, persists record, updates cache.
**Why:** Default simple QR creation.
**Used by:** `factory.QRFactory("standard")`, `batch.go` uses Standard directly.

### Walkthrough

```go
outErr := os.MkdirAll("output", os.ModePerm)
file := fmt.Sprintf("output/qr_%d.png", time.Now().UnixNano())
err := qrcode.WriteFile(data, qrcode.Medium, 256, file)
```

* Ensure output path, create unique file name, write 256x256 PNG with Medium error correction.

Persist & cache:

```go
record := models.QRRecord{Data: data, Type: "standard", FilePath: file}
if db.DB != nil { db.DB.Create(&record) }
cache.AddToCache(data, record)
```

* Good: consistent behavior with custom generator.

**Notes**

* `qrcode.WriteFile` handles file creation — error returned handled and returned to caller.
* File overwrite avoided by unique timestamp filename.

---

## `internal/models/models.go`

**What:** GORM model `QRRecord`.
**Why:** Represents DB row for QR events (generated/scanned).
**Used by:** generators and scanner.

### Walkthrough

```go
type QRRecord struct {
    ID        int       `gorm:"primaryKey;autoIncrement"`
    Data      string    `gorm:"type:text;not null"`
    Type      string    `gorm:"type:varchar(50);not null"` // standard, custom, batch, scanned
    FilePath  string    `gorm:"type:text"`
    CreatedAt time.Time `gorm:"autoCreateTime"`
}
```

* Standard GORM tags:

  * `ID` primary key auto increment.
  * `Data` text not null.
  * `Type` small varchar to categorize.
  * `CreatedAt` auto timestamp.

**Tip**

* Consider adding indexes on `Data` if you query by data frequently.
* If `Data` can be large, `type:text` is fine.

---

## `internal/scanner/scanner.go`

**What:** Opens an image file and decodes QR content using `github.com/tuotoo/qrcode`. Persists scanned content and caches it.
**Why:** Provide ability to read existing QR images.
**Used by:** `cmd/main.go` scan command.

### Walkthrough

```go
fi, err := os.Open(filePath)
qr, err := qrcode.Decode(fi)
record := models.QRRecord{Data: qr.Content, Type: "scanned", FilePath: filePath}
if db.DB != nil { db.DB.Create(&record) }
cache.AddToCache(qr.Content, record)
return qr.Content, nil
```

* Simple: open file, decode, persist in DB, cache, and return content string.

**Notes / Gotchas**

* `tuotoo/qrcode` expects certain image formats — make sure input is supported (png/jpeg) and QR not too small/blurred.
* Error messages include underlying decode error; CLI prints them.

---

# Cross-file architectural notes & suggestions (summary of design decisions)

1. **Factory + Interface** — Good: decouples main from implementations (`QRGenerator` interface). Suggestion: return error on unknown type instead of panic.

2. **Cache design** — RWMutex + map + SHA256 key: simple and correct for concurrency. Consider TTL/eviction and potential memory growth.

3. **DB handling** — global `db.DB` convenient but couples packages to global state. For testability & cleaner design, pass DB handle via constructor or use DI.

4. **Concurrency in batch** — currently spawns unbounded goroutines and ignores errors. Better: worker pool, error collection, and limit concurrency.

5. **Error handling** — several places ignore errors (CSV read, json.Unmarshal, generator.Generate inside goroutine). Fixing these will make the app robust.

6. **README vs code mismatch** — README says PostgreSQL; code uses MySQL. Sync them.

7. **CLI UX** — consider `flag` package or `cobra` for better flags/options and help messages.

8. **Security & Production** — don't store DB creds in repo; use env; consider using migrations tool (like `golang-migrate`) for production DB schema changes instead of AutoMigrate.

---

# Quick run examples (useful lines to show in script)

(यहें कैमरा पर बोलने के लिए quick snippets)

* Generate standard:
  `go run cmd/main.go generate "https://example.com"`
* Custom color:
  `go run cmd/main.go custom "hello world" "#ff0000"` (or `red`)
* Batch CSV:
  `go run cmd/main.go batch ids.csv csv` — *(note: current main expects file and optional format as third arg — double-check ordering)*
* Scan:
  `go run cmd/main.go scan output/qr_123.png`
* Cache check:
  `go run cmd/main.go cache "https://example.com"`

*(CLI arg order: main uses `os.Args[1]` command, `os.Args[2]` data/file, and for custom color `os.Args[3]`)*

---

# Final teaching tips (for the video/script)

* Use a small live demo: generate one standard QR, then `ls output/`, open PNG to show content. Then run `scan` on that PNG and show DB/cache updated. Visual proof helps retention.
* Call out the Factory pattern visually: show small diagram — `main.go -> factory -> concrete generator -> writes file -> DB & cache`.
* Emphasize concurrency gotcha with Batch and show how `sync.WaitGroup` works (explain `wg.Add`, `wg.Done`, `wg.Wait`) in a short Hindi line:
  “यहाँ हम `wg.Add(1)` करके हर काम को track कर रहे हैं, और `wg.Wait()` तब तक रोके रखता है जब तक सारे goroutine finish न हो जाएँ।”

---

अगर आप चाहें, मैं अब इसे **YouTube-style spoken script** में convert कर दूँ — line-by-line narration + on-screen prompts, short hooks, timestamps (7–8 मिनट वाली flow) — Hindi + English tech terms में, ready-to-record। सिर्फ बोलिये: **"Make video script"** और मैं पूरा spoken script दे दूँगा।
