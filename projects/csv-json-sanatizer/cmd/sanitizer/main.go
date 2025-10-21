package main

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

    fmt.Printf("Sanitization complete: Processed %d, Errors %d, Duplicates %d\n", result.Processed, result.Errors, result.Duplicates)

    if err := handler.WriteFile(*output, cleanedRows, result); err != nil {
        log.Fatalf("Write error: %v", err)
    }
}