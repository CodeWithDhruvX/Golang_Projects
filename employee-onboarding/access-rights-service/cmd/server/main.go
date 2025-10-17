package main

import (
	"access-rights-service/delivery/http"
	"access-rights-service/infrastructure/repository"
	"access-rights-service/usecase"
	"database/sql"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load("../.env")
	dsn := os.Getenv("DB_DSN")
	port := "8083"

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	accessRepo := repository.NewAccessMySQLRepository(db)
	accessUsecase := usecase.NewAccessUsecase(accessRepo)
	handler := http.NewAccessHandler(accessUsecase)

	r := gin.Default()
	v1 := r.Group("/api/v1")
	v1.POST("/grant", handler.Grant)

	r.Run(":" + port)
}
