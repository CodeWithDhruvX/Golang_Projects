package repository

import (
	"access-rights-service/domain"
	"context"
)

type AccessRepository interface {
	Save(ctx context.Context, grant domain.AccessGrant) (domain.AccessGrant, error)
}
