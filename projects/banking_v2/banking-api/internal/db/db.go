package db

import (
	"log"

	"banking-api/internal/models"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

func Connect() *gorm.DB {
	dsn := "root:root@tcp(localhost:3306)/banking_db?parseTime=true&charset=utf8mb4&collation=utf8mb4_unicode_ci"
	if dsn == "" {
		log.Fatal("DB_DSN is empty! Ensure .env is loaded.")
	}

	db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("[error] failed to initialize database, got error %v", err)
	}

	// Auto-migrate models (comment out if using manual schema.sql)
	err = db.AutoMigrate(&models.Customer{}, &models.Branch{}, &models.Account{}, &models.Transaction{}, &models.Loan{}, &models.LoanPayment{}, &models.Beneficiary{})
	if err != nil {
		log.Fatalf("AutoMigrate failed: %v", err)
	}
	log.Println("Database connected and migrated successfully!")

	return db
}
