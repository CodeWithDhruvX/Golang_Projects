package main

import (
	"fmt"
	"os"

	"github.com/skip2/go-qrcode"
)

// ----------------------
// QR Code Interface
// ----------------------
type QRCode interface {
	Generate(filename string) error
}

// ----------------------
// Text QR Code
// ----------------------
type TextQRCode struct {
	content string
}

func (t *TextQRCode) Generate(filename string) error {
	// Generate QR code from text content
	err := qrcode.WriteFile(t.content, qrcode.Medium, 256, filename)
	if err != nil {
		return err
	}
	fmt.Println("Text QR Code generated:", filename)
	return nil
}

// ----------------------
// URL QR Code
// ----------------------
type URLQRCode struct {
	url string
}

func (u *URLQRCode) Generate(filename string) error {
	// Generate QR code from URL
	err := qrcode.WriteFile(u.url, qrcode.Medium, 256, filename)
	if err != nil {
		return err
	}
	fmt.Println("URL QR Code generated:", filename)
	return nil
}

// ----------------------
// QR Code Factory
// ----------------------
type QRCodeFactory struct{}

func (f *QRCodeFactory) CreateQRCode(qrType string, data string) (QRCode, error) {
	switch qrType {
	case "text":
		return &TextQRCode{content: data}, nil
	case "url":
		return &URLQRCode{url: data}, nil
	default:
		return nil, fmt.Errorf("unsupported QR code type: %s", qrType)
	}
}

// ----------------------
// Main Function
// ----------------------
func main() {
	factory := &QRCodeFactory{}

	// Example: Text QR Code
	textQR, err := factory.CreateQRCode("text", "Hello, Golang!")
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	textQR.Generate("text_qr.png")

	// Example: URL QR Code
	urlQR, err := factory.CreateQRCode("url", "https://github.com/CodeWithDhruvX")
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	urlQR.Generate("url_qr.png")
}
