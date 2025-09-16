package api

import (
	"net/http"

	"example.com/big/internal/app/factory"

	"github.com/gin-gonic/gin"
)

func RegisterRoutes(router *gin.Engine) {
	router.POST("/generate", GenerateQRCodeHandler)
}

// GenerateQRCodeHandler handles QR code generation via REST API
func GenerateQRCodeHandler(c *gin.Context) {
	var req struct {
		Type string `json:"type"`
		Data string `json:"data"`
	}
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	f := &factory.QRCodeFactory{}
	qr, err := f.Create(req.Type, req.Data)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	filename := req.Type + "_api_qr.png"
	if err := qr.Generate(filename); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate QR code"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "QR code generated", "file": filename})
}
