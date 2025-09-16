package factory

import (
	"errors"

	"example.com/big/internal/domain/qrcode"
)

// QRCodeFactory implements Factory Method pattern for QR codes
type QRCodeFactory struct{}

// Create generates a QR code based on type
func (f *QRCodeFactory) Create(qrType, data string) (qrcode.QRCode, error) {
	switch qrType {
	case "text":
		return &qrcode.TextQRCode{Content: data}, nil
	case "url":
		return &qrcode.URLQRCode{URL: data}, nil
	default:
		return nil, errors.New("unsupported QR code type")
	}
}
