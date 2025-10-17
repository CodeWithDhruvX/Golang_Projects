package main

import (
	"database/sql"
	"it-setup-service/delivery/http"
	"it-setup-service/infrastructure/repository"
	"it-setup-service/usecase"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load("../.env")
	dsn := os.Getenv("DB_DSN")
	port := "8081"

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	provRepo := repository.NewProvisionMySQLRepository(db)
	provUsecase := usecase.NewProvisionUsecase(provRepo)
	handler := http.NewProvisionHandler(provUsecase)

	r := gin.Default()
	v1 := r.Group("/api/v1")
	v1.POST("/provision", handler.Provision)

	r.Run(":" + port)
}
