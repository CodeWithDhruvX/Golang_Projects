package usecase

import (
	"access-rights-service/domain"
	"context"
)

type AccessUsecase interface {
	Grant(ctx context.Context, req domain.GrantRequest) (domain.AccessGrant, error)
}
