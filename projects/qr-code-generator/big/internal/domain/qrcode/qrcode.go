package qrcode

import (
	"github.com/skip2/go-qrcode"
)

// QRCode interface defines the contract for all QR code types
type QRCode interface {
	Generate(filename string) error
}

// TextQRCode represents a QR code containing plain text
type TextQRCode struct {
	Content string
}

// Generate creates a PNG file for the Text QR code
func (t *TextQRCode) Generate(filename string) error {
	return qrcode.WriteFile(t.Content, qrcode.Medium, 256, filename)
}

// URLQRCode represents a QR code containing a URL
type URLQRCode struct {
	URL string
}

// Generate creates a PNG file for the URL QR code
func (u *URLQRCode) Generate(filename string) error {
	return qrcode.WriteFile(u.URL, qrcode.Medium, 256, filename)
}
