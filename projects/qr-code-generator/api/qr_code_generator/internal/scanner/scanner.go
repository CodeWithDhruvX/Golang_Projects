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
