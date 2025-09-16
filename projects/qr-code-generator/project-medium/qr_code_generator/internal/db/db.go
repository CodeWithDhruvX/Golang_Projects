package db

import (
	"fmt"
	"log"
	"os"
	"qr_code_generator/internal/models"

	"github.com/joho/godotenv"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

var DB *gorm.DB

// InitDB initializes MySQL connection
func InitDB() {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️  No .env file found, falling back to system environment variables")
	}

	// Build DSN
	dsn := fmt.Sprintf("%s:%s@tcp(localhost:3306)/%s?charset=utf8mb4&parseTime=True&loc=Local",
		os.Getenv("DB_USER"), os.Getenv("DB_PASS"), os.Getenv("DB_NAME"))

	var err error
	DB, err = gorm.Open(mysql.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}

	// Auto-migrate schema
	if err := DB.AutoMigrate(&models.QRRecord{}); err != nil {
		log.Fatalf("❌ Failed to migrate schema: %v", err)
	}

	log.Println("✅ Connected to MySQL & migrated schema.")
}
