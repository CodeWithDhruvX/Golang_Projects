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
