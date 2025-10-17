package repository

import (
	"context"
	"hr-service/domain"
)

type EmployeeRepository interface {
	Save(ctx context.Context, emp domain.Employee) (domain.Employee, error)
	FindByID(ctx context.Context, id int) (domain.Employee, error)
}
