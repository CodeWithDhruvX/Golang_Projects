package main

import (
	"database/sql"
	"email-provisioner-service/delivery/http"
	"email-provisioner-service/infrastructure/email"
	"email-provisioner-service/infrastructure/repository"
	"email-provisioner-service/usecase"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load("../.env")
	dsn := os.Getenv("DB_DSN")
	port := "8082"

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	emailRepo := repository.NewEmailMySQLRepository(db)
	sender := email.NewMockSender()
	emailUsecase := usecase.NewEmailUsecase(emailRepo, sender)
	handler := http.NewEmailHandler(emailUsecase)

	r := gin.Default()
	v1 := r.Group("/api/v1")
	v1.POST("/send", handler.Send)

	r.Run(":" + port)
}
