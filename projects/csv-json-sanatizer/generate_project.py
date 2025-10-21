import os
import zipfile
from pathlib import Path

# Project root
project_dir = Path("csv-json-sanitizer")
project_dir.mkdir(exist_ok=True)

# File contents (embedded from previous specs)
files_content = {
    "go.mod": """module csv-json-sanitizer

go 1.21

require (
    gopkg.in/yaml.v3 v3.0.1
)
""",

    "README.md": """# CSV/JSON Data Sanitizer

A Go CLI tool for cleaning and validating CSV/JSON data files.

## Setup
1. `go mod tidy`
2. Build: `go build -o sanitizer ./cmd/sanitizer`

## Usage
`./sanitizer -input data.csv -output cleaned.json -rules configs/rules.yaml`

Supports trimming, validation (e.g., email), duplicate removal, and CSV injection escaping.
""",

    "cmd/sanitizer/main.go": """package main

import (
    "flag"
    "fmt"
    "log"
    "os"

    "csv-json-sanitizer/internal/domain"
    "csv-json-sanitizer/internal/repository"
    "csv-json-sanitizer/internal/usecase"
    "gopkg.in/yaml.v3"
)

func main() {
    input := flag.String("input", "", "Input file path (CSV/JSON)")
    output := flag.String("output", "", "Output file path (CSV/JSON)")
    rulesFile := flag.String("rules", "", "Optional rules YAML file")
    flag.Parse()

    if *input == "" || *output == "" {
        log.Fatal("Input and output flags required")
    }

    handler := repository.NewFileHandler()
    rows, err := handler.ReadFile(*input)
    if err != nil {
        log.Fatalf("Read error: %v", err)
    }

    // Load rules if provided
    var rules []domain.SanitizationRule
    if *rulesFile != "" {
        data, err := os.ReadFile(*rulesFile)
        if err != nil {
            log.Fatalf("Rules load error: %v", err)
        }
        yaml.Unmarshal(data, &rules)
    } else {
        // Default rules
        rules = []domain.SanitizationRule{
            {Field: "email", Required: true, Validator: "email"},
            {Field: "name", Default: "Unknown"},
        }
    }

    service := usecase.NewSanitizeService()
    cleanedRows, result := service.Sanitize(rows, rules)

    fmt.Printf("Sanitization complete: Processed %d, Errors %d, Duplicates %d\\n", result.Processed, result.Errors, result.Duplicates)

    if err := handler.WriteFile(*output, cleanedRows, result); err != nil {
        log.Fatalf("Write error: %v", err)
    }
}
""",

    "internal/domain/entities.go": """package domain

import "time"

// Row represents a single data row from CSV or JSON.
type Row map[string]interface{}

// SanitizationRule defines configurable cleaning rules.
type SanitizationRule struct {
    Field     string `yaml:"field"`
    Required  bool   `yaml:"required"`
    Default   string `yaml:"default,omitempty"`
    Validator string `yaml:"validator,omitempty"` // e.g., "email"
}

// SanitizationResult holds processing outcomes.
type SanitizationResult struct {
    Processed int      `json:"processed"`
    Errors    int      `json:"errors"`
    Duplicates int     `json:"duplicates_removed"`
    Timestamp time.Time `json:"timestamp"`
}

// SanitizerPort defines the interface for sanitization logic.
type SanitizerPort interface {
    Sanitize([]Row, []SanitizationRule) ([]Row, SanitizationResult)
}
""",

    "internal/domain/errors.go": """package domain

import "errors"

var (
    ErrInvalidFile    = errors.New("invalid input file format")
    ErrMissingField   = errors.New("required field is missing")
    ErrValidationFail = errors.New("validation failed for field")
    ErrDuplicateRow   = errors.New("duplicate row detected")
)
""",

    "internal/usecase/sanitizer.go": """package usecase

import (
    "fmt"
    "strings"
    "time"

    "csv-json-sanitizer/internal/domain"
    "csv-json-sanitizer/pkg/utils"
)

type SanitizeService struct{}

func NewSanitizeService() domain.SanitizerPort {
    return &SanitizeService{}
}

func (s *SanitizeService) Sanitize(rows []domain.Row, rules []domain.SanitizationRule) ([]domain.Row, domain.SanitizationResult) {
    result := domain.SanitizationResult{
        Processed: len(rows),
        Timestamp: time.Now(),
    }

    cleaned := make([]domain.Row, 0, len(rows))
    seen := make(map[string]bool) // For duplicate detection via key hash

    for _, row := range rows {
        // Apply rules
        for _, rule := range rules {
            if val, exists := row[rule.Field]; exists {
                cleanedVal := utils.CleanValue(val.(string), rule)
                if rule.Required && cleanedVal == "" {
                    result.Errors++
                    continue // Skip invalid rows
                }
                row[rule.Field] = cleanedVal
            } else if rule.Required {
                row[rule.Field] = rule.Default
                result.Errors++
            }
        }

        // Check duplicates (simple hash of all fields)
        key := s.rowKey(row)
        if seen[key] {
            result.Duplicates++
            continue
        }
        seen[key] = true

        cleaned = append(cleaned, row)
    }

    return cleaned, result
}

func (s *SanitizeService) rowKey(row domain.Row) string {
    var keys []string
    for k := range row {
        keys = append(keys, fmt.Sprintf("%s:%v", k, row[k]))
    }
    return strings.Join(keys, "|")
}
""",

    "internal/repository/file_handler.go": """package repository

import (
    "encoding/csv"
    "encoding/json"
    "fmt"
    "io"
    "os"
    "path/filepath"
    "strings"

    "csv-json-sanitizer/internal/domain"
)

type FileHandler struct{}

func NewFileHandler() *FileHandler {
    return &FileHandler{}
}

// ReadFile reads CSV or JSON into rows.
func (h *FileHandler) ReadFile(path string) ([]domain.Row, error) {
    ext := strings.ToLower(filepath.Ext(path))
    file, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer file.Close()

    if ext == ".csv" {
        return h.readCSV(file)
    } else if ext == ".json" {
        return h.readJSON(file)
    }
    return nil, domain.ErrInvalidFile
}

func (h *FileHandler) readCSV(r io.Reader) ([]domain.Row, error) {
    reader := csv.NewReader(r)
    records, err := reader.ReadAll()
    if err != nil {
        return nil, err
    }

    if len(records) == 0 {
        return []domain.Row{}, nil
    }

    headers := records[0]
    rows := make([]domain.Row, 0, len(records)-1)
    for _, record := range records[1:] {
        row := make(domain.Row)
        for i, val := range record {
            if i < len(headers) {
                row[headers[i]] = strings.TrimSpace(val)
            }
        }
        rows = append(rows, row)
    }
    return rows, nil
}

func (h *FileHandler) readJSON(r io.Reader) ([]domain.Row, error) {
    var data []domain.Row
    if err := json.NewDecoder(r).Decode(&data); err != nil {
        return nil, err
    }
    return data, nil
}

// WriteFile writes rows to CSV or JSON.
func (h *FileHandler) WriteFile(path string, rows []domain.Row, result domain.SanitizationResult) error {
    file, err := os.Create(path)
    if err != nil {
        return err
    }
    defer file.Close()

    ext := strings.ToLower(filepath.Ext(path))
    if ext == ".csv" {
        return h.writeCSV(file, rows)
    } else if ext == ".json" {
        return h.writeJSON(file, rows, result)
    }
    return domain.ErrInvalidFile
}

func (h *FileHandler) writeCSV(w io.Writer, rows []domain.Row) error {
    writer := csv.NewWriter(w)
    defer writer.Flush()

    // Assume rows have consistent keys; get headers from first row
    if len(rows) == 0 {
        return nil
    }

    headers := make([]string, 0)
    for k := range rows[0] {
        headers = append(headers, k)
    }
    if err := writer.Write(headers); err != nil {
        return err
    }

    for _, row := range rows {
        record := make([]string, len(headers))
        for i, h := range headers {
            if val, ok := row[h]; ok {
                record[i] = fmt.Sprintf("%v", val)
            }
        }
        if err := writer.Write(record); err != nil {
            return err
        }
    }
    return nil
}

func (h *FileHandler) writeJSON(w io.Writer, rows []domain.Row, result domain.SanitizationResult) error {
    output := struct {
        Data   []domain.Row          `json:"data"`
        Result domain.SanitizationResult `json:"result"`
    }{rows, result}

    return json.NewEncoder(w).Encode(output)
}
""",

    "pkg/utils/validation.go": """package utils

import (
    "regexp"
    "strings"

    "csv-json-sanitizer/internal/domain"
)

var emailRegex = regexp.MustCompile(`^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,4}$`)

// CleanValue applies sanitization based on rule.
func CleanValue(val string, rule domain.SanitizationRule) string {
    // Trim whitespace
    val = strings.TrimSpace(val)

    // Handle empty/missing
    if val == "" && rule.Default != "" {
        return rule.Default
    }

    // Basic sanitization: escape CSV injection (prefix dangerous chars)
    if strings.HasPrefix(val, "=") || strings.HasPrefix(val, "+") || strings.HasPrefix(val, "-") || strings.HasPrefix(val, "@") {
        val = " " + val // Prefix space to neutralize
    }

    // Validate based on type
    if rule.Validator == "email" && !emailRegex.MatchString(val) {
        return "" // Invalid, return empty
    }

    // Remove duplicates or other simple ops can be added here
    return val
}
""",

    "configs/rules.yaml": """- field: email
  required: true
  validator: email
- field: age
  required: false
  default: "0"
- field: description
  required: false
"""
}

# Create directories
dirs = [
    project_dir / "cmd" / "sanitizer",
    project_dir / "internal" / "domain",
    project_dir / "internal" / "usecase",
    project_dir / "internal" / "repository",
    project_dir / "pkg" / "utils",
    project_dir / "configs"
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Write files
for rel_path, content in files_content.items():
    file_path = project_dir / rel_path
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content.strip())

print("Project files created successfully.")

# Zip the project
zip_path = Path("csv-json-sanitizer.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, _, filenames in os.walk(project_dir):
        for filename in filenames:
            file_path = Path(root) / filename
            arcname = file_path.relative_to(project_dir.parent)
            zipf.write(file_path, arcname)

print(f"Project zipped as {zip_path}")

# Optional: clean up the unzipped dir if desired
# import shutil
# shutil.rmtree(project_dir)
