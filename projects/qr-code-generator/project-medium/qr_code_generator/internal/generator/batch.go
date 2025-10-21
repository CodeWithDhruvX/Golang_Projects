package generator

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"strings"
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
		lines, err := reader.ReadAll()
		if err != nil {
			return "", err
		}

		for _, line := range lines {
			if len(line) > 0 {
				data := strings.TrimSpace(line[0])
				if data != "" {
					records = append(records, data)
				}
			}
		}
	} else if opts != nil && opts["format"] == "json" {
		b, err := os.ReadFile(filePath)
		if err != nil {
			return "", err
		}

		var items []map[string]interface{}
		if err := json.Unmarshal(b, &items); err != nil {
			return "", fmt.Errorf("invalid JSON: %w", err)
		}

		for _, item := range items {
			dataRaw, ok := item["data"]
			if !ok {
				continue
			}
			data := strings.TrimSpace(fmt.Sprintf("%v", dataRaw))
			if data != "" {
				records = append(records, data)
			}
		}
	} else {
		return "", fmt.Errorf("unsupported format")
	}

	if len(records) == 0 {
		return "", fmt.Errorf("no valid records found in input")
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
	return fmt.Sprintf("Batch QR generation completed: %d QR codes processed.", len(records)), nil
}
