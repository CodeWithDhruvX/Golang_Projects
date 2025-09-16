package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"qr_code_generator/internal/cache"
	"qr_code_generator/internal/db"
	"qr_code_generator/internal/factory"
	"qr_code_generator/internal/generator"
	"qr_code_generator/internal/handlers"
	"qr_code_generator/internal/scanner"

	"github.com/gorilla/mux"
)

func main() {
	// Initialize database
	db.InitDB()

	// Check if running in CLI mode
	if len(os.Args) > 1 {
		runCLI()
	} else {
		// Start HTTP server
		runServer()
	}
}

func runCLI() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run cmd/main.go [generate|custom|batch|scan|cache] <data/file>")
	}

	command := os.Args[1]

	switch command {
	case "generate":
		gen := factory.QRFactory("standard")
		file, err := gen.Generate(os.Args[2], nil)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅ Standard QR generated at:", file)

	case "custom":
		gen := factory.QRFactory("custom")
		opts := map[string]string{}
		if len(os.Args) > 3 {
			opts["color"] = os.Args[3] // e.g., "red"
		}
		file, err := gen.Generate(os.Args[2], opts)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅ Custom QR generated at:", file)

	case "batch":
		gen := &generator.BatchQRGenerator{}
		opts := map[string]string{}
		if len(os.Args) > 3 {
			opts["format"] = os.Args[3] // "csv" or "json"
		} else {
			opts["format"] = "csv"
		}
		msg, err := gen.Generate(os.Args[2], opts)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅", msg)

	case "scan":
		content, err := scanner.Scan(os.Args[2])
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println("✅ Scanned QR content:", content)

	case "cache":
		if len(os.Args) < 3 {
			log.Fatal("Usage: go run cmd/main.go cache <data>")
		}
		data := os.Args[2]
		record, found := cache.GetFromCache(data)
		if found {
			fmt.Println("✅ Cache HIT:", record)
		} else {
			fmt.Println("❌ Cache MISS for:", data)
		}

	default:
		fmt.Println("❌ Unknown command")
	}
}

func runServer() {
	r := mux.NewRouter()

	// API Endpoints
	r.HandleFunc("/api/qr/generate", handlers.GenerateQRHandler).Methods("POST")
	r.HandleFunc("/api/qr/custom", handlers.CustomQRHandler).Methods("POST")
	r.HandleFunc("/api/qr/batch", handlers.BatchQRHandler).Methods("POST")
	r.HandleFunc("/api/qr/scan", handlers.ScanQRHandler).Methods("POST")
	r.HandleFunc("/api/qr/cache/{data}", handlers.CacheQRHandler).Methods("GET")

	log.Println("🚀 Starting server on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("❌ Failed to start server: %v", err)
	}
}
