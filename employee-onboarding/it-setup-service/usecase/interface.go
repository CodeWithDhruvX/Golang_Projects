package usecase

import (
	"context"
	"it-setup-service/domain"
)

type ProvisionUsecase interface {
	Provision(ctx context.Context, req domain.ProvisionRequest) (domain.Provision, error)
}
