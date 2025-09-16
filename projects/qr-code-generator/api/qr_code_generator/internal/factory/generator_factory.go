package factory

import (
    "qr_code_generator/internal/generator"
)

// Factory Method interface
type QRGenerator interface {
    Generate(data string, opts map[string]string) (string, error)
}

// QRFactory returns appropriate generator
func QRFactory(genType string) QRGenerator {
    switch genType {
    case "standard":
        return &generator.StandardQRGenerator{}
    case "custom":
        return &generator.CustomQRGenerator{}
    case "batch":
        return &generator.BatchQRGenerator{}
    default:
        panic("❌ Unsupported generator type")
    }
}
