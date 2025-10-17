package repository

import (
	"access-rights-service/domain"
	"access-rights-service/repository"
	"context"
	"database/sql"
	"encoding/json"
)

type accessMySQLRepository struct {
	db *sql.DB
}

func NewAccessMySQLRepository(db *sql.DB) repository.AccessRepository {
	_, _ = db.Exec(`CREATE TABLE IF NOT EXISTS access_grants (
        id INT PRIMARY KEY AUTO_INCREMENT,
        employee_id INT,
        permissions JSON
    )`)
	return &accessMySQLRepository{db: db}
}

func (r *accessMySQLRepository) Save(ctx context.Context, grant domain.AccessGrant) (domain.AccessGrant, error) {
	permsJSON, _ := json.Marshal(grant.Permissions)
	result, err := r.db.ExecContext(ctx, "INSERT INTO access_grants (employee_id, permissions) VALUES (?, ?)",
		grant.EmployeeID, string(permsJSON))
	if err != nil {
		return domain.AccessGrant{}, err
	}
	id, _ := result.LastInsertId()
	grant.ID = int(id)
	return grant, nil
}
