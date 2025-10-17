package repository

import (
	"context"
	"database/sql"
	"it-setup-service/domain"
	"it-setup-service/repository"
)

type provisionMySQLRepository struct {
	db *sql.DB
}

func NewProvisionMySQLRepository(db *sql.DB) repository.ProvisionRepository {
	_, _ = db.Exec(`CREATE TABLE IF NOT EXISTS it_provisions (
        id INT PRIMARY KEY AUTO_INCREMENT,
        employee_id INT,
        device VARCHAR(255),
        status VARCHAR(100)
    )`)
	return &provisionMySQLRepository{db: db}
}

func (r *provisionMySQLRepository) Save(ctx context.Context, prov domain.Provision) (domain.Provision, error) {
	result, err := r.db.ExecContext(ctx, "INSERT INTO it_provisions (employee_id, device, status) VALUES (?, ?, ?)",
		prov.EmployeeID, prov.Device, prov.Status)
	if err != nil {
		return domain.Provision{}, err
	}
	id, _ := result.LastInsertId()
	prov.ID = int(id)
	return prov, nil
}
