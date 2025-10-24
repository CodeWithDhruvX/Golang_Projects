package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/go-sql-driver/mysql"

	"cinema-booking/config"
	"cinema-booking/internal/handler/http"
)

func main() {
	cfg := config.LoadConfig()

	// DB connection
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true",
		cfg.DBUser, cfg.DBPassword, cfg.DBHost, cfg.DBPort, cfg.DBName)
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Init schema
	initSchema(db)

	app := &http.App{}
	app.Initialize(db, cfg)
	app.Run(cfg.ServerPort)
}

// ... (imports and main unchanged)

func initSchema(db *sql.DB) {
	// Order: Base tables (no FKs) first, then dependents
	queries := []string{
		// Database setup
		`CREATE DATABASE IF NOT EXISTS cinema_db`,
		`USE cinema_db`,

		// Independent/base tables (no incoming FKs)
		`CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            duration_minutes INT NOT NULL,
            genre VARCHAR(100)
        )`,
		`CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )`,
		`CREATE TABLE IF NOT EXISTS theaters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            capacity INT NOT NULL
        )`,

		// Dependent tables (FK to bases)
		`CREATE TABLE IF NOT EXISTS shows (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT,
            theater_id INT,
            show_time DATETIME NOT NULL,
            total_seats INT NOT NULL,
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (theater_id) REFERENCES theaters(id)
        )`,
		`CREATE TABLE IF NOT EXISTS seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            show_id INT,
            seat_number VARCHAR(50) NOT NULL,
            is_booked BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (show_id) REFERENCES shows(id)
        )`,
		`CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            show_id INT,
            seat_ids JSON,
            user_id INT,
            user_name VARCHAR(255) NOT NULL,
            booked_at DATETIME NOT NULL,
            FOREIGN KEY (show_id) REFERENCES shows(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )`,
	}

	for _, q := range queries {
		if _, err := db.Exec(q); err != nil {
			log.Printf("Schema init error: %v (query: %s)", err, q) // Log query for debug
		}
	}
	log.Println("Schema initialization complete") // Success log
}

// ... (main function unchanged)
