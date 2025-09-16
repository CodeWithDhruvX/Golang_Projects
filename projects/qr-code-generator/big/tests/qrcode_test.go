package tests

import (
	"os"
	"testing"

	"big/internal/app/factory"
)

func TestTextQRCodeGeneration(t *testing.T) {
	f := &factory.QRCodeFactory{}
	qr, _ := f.Create("text", "Test QR")
	err := qr.Generate("test_qr.png")
	if err != nil {
		t.Errorf("Failed to generate QR code: %v", err)
	}
	if _, err := os.Stat("test_qr.png"); os.IsNotExist(err) {
		t.Errorf("QR code file not found")
	}
	os.Remove("test_qr.png")
}

func TestURLQRCodeGeneration(t *testing.T) {
	f := &factory.QRCodeFactory{}
	qr, _ := f.Create("url", "https://github.com/CodeWithDhruvX")
	err := qr.Generate("test_url_qr.png")
	if err != nil {
		t.Errorf("Failed to generate QR code: %v", err)
	}
	if _, err := os.Stat("test_url_qr.png"); os.IsNotExist(err) {
		t.Errorf("QR code file not found")
	}
	os.Remove("test_url_qr.png")
}
