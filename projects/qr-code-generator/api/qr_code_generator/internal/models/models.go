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
