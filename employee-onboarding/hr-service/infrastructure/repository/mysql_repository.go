package infrastructure

import (
	"context"
	"database/sql"
	"fmt"
	"hr-service/domain"
	"hr-service/repository" // Import the core interface
)

type employeeMySQLRepository struct {
	db *sql.DB
}

func NewEmployeeMySQLRepository(db *sql.DB) repository.EmployeeRepository {
	sqlQuery := `CREATE TABLE IF NOT EXISTS employees (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        address VARCHAR(255),
        role VARCHAR(100)
    )`
	_, err := db.Exec(sqlQuery)
	if err != nil {
		fmt.Printf("Table creation error: %v\n", err)
	}
	return &employeeMySQLRepository{db: db}
}

func (r *employeeMySQLRepository) Save(ctx context.Context, emp domain.Employee) (domain.Employee, error) {
	result, err := r.db.ExecContext(ctx, "INSERT INTO employees (name, email, address, role) VALUES (?, ?, ?, ?)",
		emp.Name, emp.Email, emp.Address, emp.Role)
	if err != nil {
		return domain.Employee{}, err
	}
	id, _ := result.LastInsertId()
	emp.ID = int(id)
	return emp, nil
}

func (r *employeeMySQLRepository) FindByID(ctx context.Context, id int) (domain.Employee, error) {
	var emp domain.Employee
	err := r.db.QueryRowContext(ctx, "SELECT id, name, email, address, role FROM employees WHERE id = ?", id).
		Scan(&emp.ID, &emp.Name, &emp.Email, &emp.Address, &emp.Role)
	return emp, err
}
