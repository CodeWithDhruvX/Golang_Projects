package usecase

import (
	"context"
	"employee-onboarding/common/httpclient"
	"hr-service/domain"
	"hr-service/infrastructure/http"
	"hr-service/repository"
)

type employeeUsecase struct {
	repo         repository.EmployeeRepository
	itClient     *httpclient.Client
	emailClient  *httpclient.Client
	accessClient *httpclient.Client
}

func NewEmployeeUsecase(repo repository.EmployeeRepository, itClient, emailClient, accessClient *httpclient.Client) EmployeeUsecase {
	return &employeeUsecase{repo: repo, itClient: itClient, emailClient: emailClient, accessClient: accessClient}
}

func (u *employeeUsecase) Onboard(ctx context.Context, req domain.OnboardingRequest) (domain.Employee, error) {
	emp := req.Employee
	saved, err := u.repo.Save(ctx, emp)
	if err != nil {
		return domain.Employee{}, err
	}
	// Orchestrate: Call other services
	_, _ = http.CallITProvision(u.itClient, ctx, saved.ID)
	_, _ = http.CallEmailSend(u.emailClient, ctx, saved)
	_, _ = http.CallAccessGrant(u.accessClient, ctx, saved.ID)
	return saved, nil
}

func (u *employeeUsecase) GetByID(ctx context.Context, id int) (domain.Employee, error) {
	return u.repo.FindByID(ctx, id)
}
