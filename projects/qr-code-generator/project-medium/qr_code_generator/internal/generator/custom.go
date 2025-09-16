package generator

import (
	"fmt"
	"image/color"
	"os"
	"strconv"
	"strings"
	"time"

	"qr_code_generator/internal/cache"
	"qr_code_generator/internal/db"
	"qr_code_generator/internal/models"

	"github.com/skip2/go-qrcode"
)

// CustomQRGenerator creates QR codes with optional color customizations.
type CustomQRGenerator struct{}

func (g *CustomQRGenerator) Generate(data string, opts map[string]string) (string, error) {
	// ensure output directory exists
	if err := os.MkdirAll("output", os.ModePerm); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	file := fmt.Sprintf("output/custom_qr_%d.png", time.Now().UnixNano())

	qr, err := qrcode.New(data, qrcode.High)
	if err != nil {
		return "", err
	}

	// default foreground is black
	fg := color.RGBA{0, 0, 0, 255}
	// default background is white
	bg := color.RGBA{255, 255, 255, 255}

	if opts != nil {
		if c, ok := opts["color"]; ok && strings.TrimSpace(c) != "" {
			if parsed, perr := parseColor(strings.TrimSpace(c)); perr == nil {
				fg = parsed
			}
		}
		if c, ok := opts["bg"]; ok && strings.TrimSpace(c) != "" {
			if parsed, perr := parseColor(strings.TrimSpace(c)); perr == nil {
				bg = parsed
			}
		}
	}

	qr.ForegroundColor = fg
	qr.BackgroundColor = bg

	if err := qr.WriteFile(256, file); err != nil {
		return "", err
	}

	record := models.QRRecord{Data: data, Type: "custom", FilePath: file}
	if db.DB != nil {
		db.DB.Create(&record)
	}
	cache.AddToCache(data, record)

	return file, nil
}

// parseColor accepts named colors or hex strings (#RRGGBB, RRGGBB, #RGB)
func parseColor(s string) (color.RGBA, error) {
	switch strings.ToLower(s) {
	case "black":
		return color.RGBA{0, 0, 0, 255}, nil
	case "white":
		return color.RGBA{255, 255, 255, 255}, nil
	case "red":
		return color.RGBA{255, 0, 0, 255}, nil
	case "green":
		return color.RGBA{0, 255, 0, 255}, nil
	case "blue":
		return color.RGBA{0, 0, 255, 255}, nil
	case "yellow":
		return color.RGBA{255, 255, 0, 255}, nil
	case "purple":
		return color.RGBA{128, 0, 128, 255}, nil
	case "orange":
		return color.RGBA{255, 165, 0, 255}, nil
	case "gray", "grey":
		return color.RGBA{128, 128, 128, 255}, nil
	}

	// hex parsing
	s = strings.TrimPrefix(s, "#")
	// expand 3-digit form, e.g. "0f8" -> "00ff88"
	if len(s) == 3 {
		s = fmt.Sprintf("%c%c%c%c%c%c", s[0], s[0], s[1], s[1], s[2], s[2])
	}
	if len(s) != 6 {
		return color.RGBA{}, fmt.Errorf("unsupported color format: %s", s)
	}
	r64, err := strconv.ParseUint(s[0:2], 16, 8)
	if err != nil {
		return color.RGBA{}, err
	}
	g64, err := strconv.ParseUint(s[2:4], 16, 8)
	if err != nil {
		return color.RGBA{}, err
	}
	b64, err := strconv.ParseUint(s[4:6], 16, 8)
	if err != nil {
		return color.RGBA{}, err
	}
	return color.RGBA{uint8(r64), uint8(g64), uint8(b64), 255}, nil
}
