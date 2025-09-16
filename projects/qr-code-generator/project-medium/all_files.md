````

## qr_code_generator/README.md
```markdown
# qr_code_generator

Complete Go implementation of a QR code generator demonstrating:
- Factory Method pattern
- Thread-safe map cache
- PostgreSQL integration with GORM
- Standard, Custom and Batch QR generators
- QR scanner (using tuotoo/qrcode)


https://chatgpt.com/c/68c916d1-a1fc-8323-8b24-3da67e29af4b
```

## qr_code_generator/cmd/main.go
```go
package main

import (
	"fmt"
	"log"
	"os"
	"qr_code_generator/internal/cache"
	"qr_code_generator/internal/db"
	"qr_code_generator/internal/factory"
	"qr_code_generator/internal/generator"
	"qr_code_generator/internal/scanner"
)

func main() {
	db.InitDB()

	if len(os.Args) < 2 {
		log.Fatal("Usage: go run cmd/main.go [generate|custom|batch|scan|cache] <data/file>")
	}

	command := os.Args[1]

	switch command {
	case "generate":
		gen := factory.QRFactory("standard")
		file, err := gen.Generate(os.Args[2], nil)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅ Standard QR generated at:", file)

	case "custom":
		gen := factory.QRFactory("custom")
		opts := map[string]string{}
		if len(os.Args) > 3 {
			opts["color"] = os.Args[3] // e.g., "red"
		}
		file, err := gen.Generate(os.Args[2], opts)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅ Custom QR generated at:", file)

	case "batch":
		gen := &generator.BatchQRGenerator{}
		opts := map[string]string{}
		if len(os.Args) > 3 {
			opts["format"] = os.Args[3] // "csv" or "json"
		} else {
			opts["format"] = "csv"
		}
		msg, err := gen.Generate(os.Args[2], opts)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅", msg)

	case "scan":
		content, err := scanner.Scan(os.Args[2])
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅ Scanned QR content:", content)

	case "cache":
		if len(os.Args) < 3 {
			log.Fatal("Usage: go run cmd/main.go cache <data>")
		}
		data := os.Args[2]
		record, found := cache.GetFromCache(data)
		if found {
			fmt.Println("✅ Cache HIT:", record)
		} else {
			fmt.Println("❌ Cache MISS for:", data)
		}

	default:
		fmt.Println("❌ Unknown command")
	}
}
```

## qr_code_generator/internal/cache/cache.go
```go
package cache

import (
    "crypto/sha256"
    "encoding/hex"
    "qr_code_generator/internal/models"
    "sync"
)

// thread-safe hash table cache
var mu sync.RWMutex
var qrCache = make(map[string]models.QRRecord)

// hash function for consistent keys
func hash(data string) string {
    h := sha256.Sum256([]byte(data))
    return hex.EncodeToString(h[:])
}

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

## qr_code_generator/internal/db/db.go
```go
package db

import (
	"fmt"
	"log"
	"os"
	"qr_code_generator/internal/models"

	"github.com/joho/godotenv"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

var DB *gorm.DB

// InitDB initializes MySQL connection
func InitDB() {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️  No .env file found, falling back to system environment variables")
	}

	// Build DSN
	dsn := fmt.Sprintf("%s:%s@tcp(localhost:3306)/%s?charset=utf8mb4&parseTime=True&loc=Local",
		os.Getenv("DB_USER"), os.Getenv("DB_PASS"), os.Getenv("DB_NAME"))

	var err error
	DB, err = gorm.Open(mysql.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}

	// Auto-migrate schema
	if err := DB.AutoMigrate(&models.QRRecord{}); err != nil {
		log.Fatalf("❌ Failed to migrate schema: %v", err)
	}

	log.Println("✅ Connected to MySQL & migrated schema.")
}
```

## qr_code_generator/internal/factory/generator_factory.go
```go
package factory

import (
    "qr_code_generator/internal/generator"
)

// Factory Method interface
type QRGenerator interface {
    Generate(data string, opts map[string]string) (string, error)
}

// QRFactory returns appropriate generator
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

## qr_code_generator/internal/generator/batch.go
```go
package generator

import (
    "encoding/csv"
    "encoding/json"
    "fmt"
    "os"
    "sync"
)

type BatchQRGenerator struct{}

func (g *BatchQRGenerator) Generate(filePath string, opts map[string]string) (string, error) {
    var records []string

    if opts != nil && opts["format"] == "csv" {
        file, err := os.Open(filePath)
        if err != nil {
            return "", err
        }
        defer file.Close()

        reader := csv.NewReader(file)
        lines, _ := reader.ReadAll()
        for _, line := range lines {
            if len(line) > 0 {
                records = append(records, line[0])
            }
        }
    } else if opts != nil && opts["format"] == "json" {
        b, err := os.ReadFile(filePath)
        if err != nil {
            return "", err
        }
        json.Unmarshal(b, &records)
    } else {
        return "", fmt.Errorf("unsupported format")
    }

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
    return "Batch QR generation completed.", nil
}
```

## qr_code_generator/internal/generator/custom.go
```go
package generator

import (
	"fmt"
	"image/color"
	"os"
	"strconv"
	"strings"
	"time"

	"qr_code_generator/internal/cache"
	"qr_code_generator/internal/db"
	"qr_code_generator/internal/models"

	"github.com/skip2/go-qrcode"
)

// CustomQRGenerator creates QR codes with optional color customizations.
type CustomQRGenerator struct{}

func (g *CustomQRGenerator) Generate(data string, opts map[string]string) (string, error) {
	// ensure output directory exists
	if err := os.MkdirAll("output", os.ModePerm); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	file := fmt.Sprintf("output/custom_qr_%d.png", time.Now().UnixNano())

	qr, err := qrcode.New(data, qrcode.High)
	if err != nil {
		return "", err
	}

	// default foreground is black
	fg := color.RGBA{0, 0, 0, 255}
	// default background is white
	bg := color.RGBA{255, 255, 255, 255}

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

	if err := qr.WriteFile(256, file); err != nil {
		return "", err
	}

	record := models.QRRecord{Data: data, Type: "custom", FilePath: file}
	if db.DB != nil {
		db.DB.Create(&record)
	}
	cache.AddToCache(data, record)

	return file, nil
}

// parseColor accepts named colors or hex strings (#RRGGBB, RRGGBB, #RGB)
func parseColor(s string) (color.RGBA, error) {
	switch strings.ToLower(s) {
	case "black":
		return color.RGBA{0, 0, 0, 255}, nil
	case "white":
		return color.RGBA{255, 255, 255, 255}, nil
	case "red":
		return color.RGBA{255, 0, 0, 255}, nil
	case "green":
		return color.RGBA{0, 255, 0, 255}, nil
	case "blue":
		return color.RGBA{0, 0, 255, 255}, nil
	case "yellow":
		return color.RGBA{255, 255, 0, 255}, nil
	case "purple":
		return color.RGBA{128, 0, 128, 255}, nil
	case "orange":
		return color.RGBA{255, 165, 0, 255}, nil
	case "gray", "grey":
		return color.RGBA{128, 128, 128, 255}, nil
	}

	// hex parsing
	s = strings.TrimPrefix(s, "#")
	// expand 3-digit form, e.g. "0f8" -> "00ff88"
	if len(s) == 3 {
		s = fmt.Sprintf("%c%c%c%c%c%c", s[0], s[0], s[1], s[1], s[2], s[2])
	}
	if len(s) != 6 {
		return color.RGBA{}, fmt.Errorf("unsupported color format: %s", s)
	}
	r64, err := strconv.ParseUint(s[0:2], 16, 8)
	if err != nil {
		return color.RGBA{}, err
	}
	g64, err := strconv.ParseUint(s[2:4], 16, 8)
	if err != nil {
		return color.RGBA{}, err
	}
	b64, err := strconv.ParseUint(s[4:6], 16, 8)
	if err != nil {
		return color.RGBA{}, err
	}
	return color.RGBA{uint8(r64), uint8(g64), uint8(b64), 255}, nil
}
```

## qr_code_generator/internal/generator/standard.go
```go
package generator

import (
	"fmt"
	"os"
	"time"

	"qr_code_generator/internal/cache"
	"qr_code_generator/internal/db"
	"qr_code_generator/internal/models"

	"github.com/skip2/go-qrcode"
)

type StandardQRGenerator struct{}

func (g *StandardQRGenerator) Generate(data string, opts map[string]string) (string, error) {

	// inside your generator function
	outErr := os.MkdirAll("output", os.ModePerm) // <-- create directory if missing
	if outErr != nil {
		return "", fmt.Errorf("failed to create output directory: %w", outErr)
	}

	file := fmt.Sprintf("output/qr_%d.png", time.Now().UnixNano())
	err := qrcode.WriteFile(data, qrcode.Medium, 256, file)
	if err != nil {
		return "", fmt.Errorf("failed to generate QR: %w", err)
	}

	record := models.QRRecord{Data: data, Type: "standard", FilePath: file}
	if db.DB != nil {
		db.DB.Create(&record)
	}
	cache.AddToCache(data, record)

	return file, nil
}
```

## qr_code_generator/internal/models/models.go
```go
package models

import "time"

// QRRecord represents a QR code record in DB/cache
type QRRecord struct {
    ID        int       `gorm:"primaryKey;autoIncrement"`
    Data      string    `gorm:"type:text;not null"`
    Type      string    `gorm:"type:varchar(50);not null"` // standard, custom, batch, scanned
    FilePath  string    `gorm:"type:text"`
    CreatedAt time.Time `gorm:"autoCreateTime"`
}
```

## qr_code_generator/internal/scanner/scanner.go
```go
package scanner

import (
    "fmt"
    "os"
    "qr_code_generator/internal/cache"
    "qr_code_generator/internal/db"
    "qr_code_generator/internal/models"

    "github.com/tuotoo/qrcode"
)

func Scan(filePath string) (string, error) {
    fi, err := os.Open(filePath)
    if err != nil {
        return "", fmt.Errorf("failed to open file: %w", err)
    }
    defer fi.Close()

    qr, err := qrcode.Decode(fi)
    if err != nil {
        return "", fmt.Errorf("failed to decode QR: %w", err)
    }

    record := models.QRRecord{Data: qr.Content, Type: "scanned", FilePath: filePath}
    if db.DB != nil {
        db.DB.Create(&record)
    }
    cache.AddToCache(qr.Content, record)

    return qr.Content, nil
}


````




give me this cli app into the api app