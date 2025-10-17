package main

import (
	"database/sql"
	"employee-onboarding/common/httpclient"
	"hr-service/delivery/http"
	infrastructure "hr-service/infrastructure/repository" // Imports the impl package (named "infrastructure")
	"hr-service/usecase"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load("../.env") // Load shared env
	dsn := os.Getenv("DB_DSN")
	port := os.Getenv("PORT")
	itURL := os.Getenv("IT_URL")
	emailURL := os.Getenv("EMAIL_URL")
	accessURL := os.Getenv("ACCESS_URL")
	log.Printf("DSN: %s", dsn)
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	empRepo := infrastructure.NewEmployeeMySQLRepository(db) // Changed: Use "infrastructure." prefix
	itClient := httpclient.NewClient(itURL)
	emailClient := httpclient.NewClient(emailURL)
	accessClient := httpclient.NewClient(accessURL)
	empUsecase := usecase.NewEmployeeUsecase(empRepo, itClient, emailClient, accessClient)
	handler := http.NewEmployeeHandler(empUsecase)

	r := gin.Default()
	v1 := r.Group("/api/v1")
	v1.POST("/onboard", handler.Onboard)
	v1.GET("/employee/:id", handler.GetByID)

	r.Run(":" + port)
}
