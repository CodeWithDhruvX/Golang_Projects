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
