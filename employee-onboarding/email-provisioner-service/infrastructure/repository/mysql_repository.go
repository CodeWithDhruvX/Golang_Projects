package repository

import (
	"context"
	"database/sql"
	"email-provisioner-service/domain"
	"email-provisioner-service/repository"
)

type emailMySQLRepository struct {
	db *sql.DB
}

func NewEmailMySQLRepository(db *sql.DB) repository.EmailRepository {
	_, _ = db.Exec(`CREATE TABLE IF NOT EXISTS email_logs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        employee_id INT,
        to_email VARCHAR(255),
        subject VARCHAR(255),
        status VARCHAR(100)
    )`)
	return &emailMySQLRepository{db: db}
}

func (r *emailMySQLRepository) Save(ctx context.Context, log domain.EmailLog) (domain.EmailLog, error) {
	result, err := r.db.ExecContext(ctx, "INSERT INTO email_logs (employee_id, to_email, subject, status) VALUES (?, ?, ?, ?)",
		log.EmployeeID, log.To, log.Subject, log.Status)
	if err != nil {
		return domain.EmailLog{}, err
	}
	id, _ := result.LastInsertId()
	log.ID = int(id)
	return log, nil
}
