package usecase

import (
	"context"
	"it-setup-service/domain"
	"it-setup-service/repository"
)

type provisionUsecase struct {
	repo repository.ProvisionRepository
}

func NewProvisionUsecase(repo repository.ProvisionRepository) ProvisionUsecase {
	return &provisionUsecase{repo: repo}
}

func (u *provisionUsecase) Provision(ctx context.Context, req domain.ProvisionRequest) (domain.Provision, error) {
	prov := domain.Provision{EmployeeID: req.EmployeeID, Device: "Laptop", Status: "Provisioned"}
	return u.repo.Save(ctx, prov)
}
