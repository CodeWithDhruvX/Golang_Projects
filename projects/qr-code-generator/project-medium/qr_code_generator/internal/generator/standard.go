package generator

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"qr_code_generator/internal/db"
	"qr_code_generator/internal/models"

	"github.com/google/uuid"
	"github.com/skip2/go-qrcode"
)

type StandardQRGenerator struct{}

func (g *StandardQRGenerator) Generate(input string, opts map[string]string) (string, error) {
	// Detect if input is a file
	if fileInfo, err := os.Stat(input); err == nil && !fileInfo.IsDir() {
		ext := strings.ToLower(filepath.Ext(input))
		switch ext {
		case ".csv":
			return g.generateFromCSV(input)
		case ".json":
			return g.generateFromJSON(input)
		}
	}

	// Otherwise, treat as single data string
	return g.generateSingle(input)
}

// ---------------- Single QR ----------------
func (g *StandardQRGenerator) generateSingle(data string) (string, error) {
	data = strings.TrimSpace(data)
	if data == "" {
		return "", fmt.Errorf("data cannot be empty")
	}

	// Check DB for existing record
	var record models.QRRecord
	if db.DB != nil {
		err := db.DB.Where("data = ?", data).First(&record).Error
		if err == nil {
			fmt.Printf("⚡ Found in DB: %s\n", data)
			return record.FilePath, nil
		}
	}

	// Ensure output folder exists
	if err := os.MkdirAll("output", os.ModePerm); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	file := fmt.Sprintf("output/qr_%s.png", uuid.New().String())
	if err := qrcode.WriteFile(data, qrcode.Medium, 256, file); err != nil {
		return "", fmt.Errorf("failed to generate QR: %w", err)
	}

	// Save to DB
	record = models.QRRecord{Data: data, Type: "standard", FilePath: file}
	if db.DB != nil {
		db.DB.Create(&record)
	}

	fmt.Printf("✅ Generated QR for: %s\n", data)
	return file, nil
}

// ---------------- CSV Batch ----------------
func (g *StandardQRGenerator) generateFromCSV(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to open CSV: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	headers, err := reader.Read()
	if err != nil {
		return "", fmt.Errorf("failed to read CSV headers: %w", err)
	}

	dataIdx, typeIdx := -1, -1
	for i, h := range headers {
		switch strings.ToLower(strings.TrimSpace(h)) {
		case "data":
			dataIdx = i
		case "type":
			typeIdx = i
		}
	}
	if dataIdx == -1 {
		return "", fmt.Errorf("CSV missing 'data' column")
	}

	if err := os.MkdirAll("output", os.ModePerm); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	count := 0
	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			fmt.Printf("⚠️ Skipping row due to read error: %v\n", err)
			continue
		}

		if len(row) <= dataIdx {
			fmt.Printf("⚠️ Skipping row: insufficient columns\n")
			continue
		}

		data := strings.TrimSpace(row[dataIdx])
		if data == "" {
			fmt.Printf("⚠️ Skipping row: empty data\n")
			continue
		}

		qrType := "standard"
		if typeIdx >= 0 && len(row) > typeIdx {
			t := strings.TrimSpace(row[typeIdx])
			if t != "" {
				qrType = t
			}
		}

		// DB check
		var record models.QRRecord
		if db.DB != nil {
			err := db.DB.Where("data = ?", data).First(&record).Error
			if err == nil {
				fmt.Printf("⚡ Found in DB: %s\n", data)
				count++
				continue
			}
		}

		file := fmt.Sprintf("output/qr_%s.png", uuid.New().String())
		if err := qrcode.WriteFile(data, qrcode.Medium, 256, file); err != nil {
			fmt.Printf("❌ Failed for '%s': %v\n", data, err)
			continue
		}

		record = models.QRRecord{Data: data, Type: qrType, FilePath: file}
		if db.DB != nil {
			db.DB.Create(&record)
		}

		fmt.Printf("✅ Generated QR for: %s\n", data)
		count++
	}

	summary := fmt.Sprintf("📦 CSV batch completed! %d QR codes processed.", count)
	fmt.Println(summary)
	return summary, nil
}

// ---------------- JSON Batch ----------------
func (g *StandardQRGenerator) generateFromJSON(filePath string) (string, error) {
	file, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read JSON file: %w", err)
	}

	var items []map[string]interface{}
	if err := json.Unmarshal(file, &items); err != nil {
		return "", fmt.Errorf("invalid JSON format: %w", err)
	}

	if len(items) == 0 {
		return "", fmt.Errorf("JSON file is empty")
	}

	if err := os.MkdirAll("output", os.ModePerm); err != nil {
		return "", fmt.Errorf("failed to create output folder: %w", err)
	}

	count := 0
	for idx, item := range items {
		dataRaw, ok := item["data"]
		if !ok {
			fmt.Printf("⚠️ Skipping item %d: missing 'data'\n", idx)
			continue
		}

		data := strings.TrimSpace(fmt.Sprintf("%v", dataRaw))
		if data == "" {
			fmt.Printf("⚠️ Skipping item %d: empty 'data'\n", idx)
			continue
		}

		qrType := "standard"
		if tRaw, exists := item["type"]; exists {
			t := strings.TrimSpace(fmt.Sprintf("%v", tRaw))
			if t != "" {
				qrType = t
			}
		}

		// DB check
		var record models.QRRecord
		if db.DB != nil {
			err := db.DB.Where("data = ?", data).First(&record).Error
			if err == nil {
				fmt.Printf("⚡ Found in DB: %s\n", data)
				count++
				continue
			}
		}

		file := fmt.Sprintf("output/qr_%s.png", uuid.New().String())
		if err := qrcode.WriteFile(data, qrcode.Medium, 256, file); err != nil {
			fmt.Printf("❌ Failed for '%s': %v\n", data, err)
			continue
		}

		record = models.QRRecord{Data: data, Type: qrType, FilePath: file}
		if db.DB != nil {
			db.DB.Create(&record)
		}

		fmt.Printf("✅ Generated QR for: %s\n", data)
		count++
	}

	summary := fmt.Sprintf("📦 JSON batch completed! %d QR codes processed.", count)
	fmt.Println(summary)
	return summary, nil
}
