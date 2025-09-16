package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"qr_code_generator/internal/cache"
	"qr_code_generator/internal/factory"
	"qr_code_generator/internal/generator"
	"qr_code_generator/internal/scanner"

	"github.com/gorilla/mux"
)

type generateRequest struct {
	Data string `json:"data"`
}

type customRequest struct {
	Data  string `json:"data"`
	Color string `json:"color"`
	Bg    string `json:"bg"`
}

type response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data"`
	Error   string      `json:"error,omitempty"`
}

func GenerateQRHandler(w http.ResponseWriter, r *http.Request) {
	var req generateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	if req.Data == "" {
		sendError(w, "Data is required", http.StatusBadRequest)
		return
	}

	gen := factory.QRFactory("standard")
	file, err := gen.Generate(req.Data, nil)
	if err != nil {
		sendError(w, fmt.Sprintf("Failed to generate QR: %v", err), http.StatusInternalServerError)
		return
	}

	sendResponse(w, map[string]string{"file": file}, http.StatusOK)
}

func CustomQRHandler(w http.ResponseWriter, r *http.Request) {
	var req customRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	if req.Data == "" {
		sendError(w, "Data is required", http.StatusBadRequest)
		return
	}

	gen := factory.QRFactory("custom")
	opts := map[string]string{}
	if req.Color != "" {
		opts["color"] = req.Color
	}
	if req.Bg != "" {
		opts["bg"] = req.Bg
	}
	file, err := gen.Generate(req.Data, opts)
	if err != nil {
		sendError(w, fmt.Sprintf("Failed to generate custom QR: %v", err), http.StatusInternalServerError)
		return
	}

	sendResponse(w, map[string]string{"file": file}, http.StatusOK)
}

func BatchQRHandler(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(10 << 20); err != nil { // 10MB max
		sendError(w, "Failed to parse form", http.StatusBadRequest)
		return
	}

	file, _, err := r.FormFile("file")
	if err != nil {
		sendError(w, "File is required", http.StatusBadRequest)
		return
	}
	defer file.Close()

	format := r.FormValue("format")
	if format == "" {
		format = "csv"
	}
	if format != "csv" && format != "json" {
		sendError(w, "Unsupported format", http.StatusBadRequest)
		return
	}

	// Save uploaded file temporarily
	tempFile, err := os.CreateTemp("", "qr-batch-*.tmp")
	if err != nil {
		sendError(w, "Failed to create temp file", http.StatusInternalServerError)
		return
	}
	defer os.Remove(tempFile.Name())
	defer tempFile.Close()

	_, err = io.Copy(tempFile, file)
	if err != nil {
		sendError(w, "Failed to save file", http.StatusInternalServerError)
		return
	}

	gen := &generator.BatchQRGenerator{}
	opts := map[string]string{"format": format}
	msg, err := gen.Generate(tempFile.Name(), opts)
	if err != nil {
		sendError(w, fmt.Sprintf("Failed to process batch: %v", err), http.StatusInternalServerError)
		return
	}

	sendResponse(w, map[string]string{"message": msg}, http.StatusOK)
}

func ScanQRHandler(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(10 << 20); err != nil { // 10MB max
		sendError(w, "Failed to parse form", http.StatusBadRequest)
		return
	}

	file, _, err := r.FormFile("file")
	if err != nil {
		sendError(w, "File is required", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Save uploaded file temporarily
	tempFile, err := os.CreateTemp("", "qr-scan-*.png")
	if err != nil {
		sendError(w, "Failed to create temp file", http.StatusInternalServerError)
		return
	}
	defer os.Remove(tempFile.Name())
	defer tempFile.Close()

	_, err = io.Copy(tempFile, file)
	if err != nil {
		sendError(w, "Failed to save file", http.StatusInternalServerError)
		return
	}

	content, err := scanner.Scan(tempFile.Name())
	if err != nil {
		sendError(w, fmt.Sprintf("Failed to scan QR: %v", err), http.StatusInternalServerError)
		return
	}

	sendResponse(w, map[string]string{"content": content}, http.StatusOK)
}

func CacheQRHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	data := vars["data"]
	if data == "" {
		sendError(w, "Data is required", http.StatusBadRequest)
		return
	}

	record, found := cache.GetFromCache(data)
	if !found {
		sendError(w, fmt.Sprintf("Cache MISS for: %s", data), http.StatusNotFound)
		return
	}

	sendResponse(w, map[string]interface{}{"record": record}, http.StatusOK)
}

func sendResponse(w http.ResponseWriter, data interface{}, status int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(response{Success: true, Data: data})
}

func sendError(w http.ResponseWriter, errorMsg string, status int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(response{Success: false, Error: errorMsg})
}
