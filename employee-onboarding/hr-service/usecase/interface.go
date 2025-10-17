package usecase

import (
	"context"
	"hr-service/domain"
)

type EmployeeUsecase interface {
	Onboard(ctx context.Context, req domain.OnboardingRequest) (domain.Employee, error)
	GetByID(ctx context.Context, id int) (domain.Employee, error)
}
