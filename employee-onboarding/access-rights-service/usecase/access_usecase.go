package usecase

import (
	"access-rights-service/domain"
	"access-rights-service/repository"
	"context"
)

type accessUsecase struct {
	repo repository.AccessRepository
}

func NewAccessUsecase(repo repository.AccessRepository) AccessUsecase {
	return &accessUsecase{repo: repo}
}

func (u *accessUsecase) Grant(ctx context.Context, req domain.GrantRequest) (domain.AccessGrant, error) {
	grant := domain.AccessGrant{EmployeeID: req.EmployeeID, Permissions: []string{"read", "write"}}
	return u.repo.Save(ctx, grant)
}
