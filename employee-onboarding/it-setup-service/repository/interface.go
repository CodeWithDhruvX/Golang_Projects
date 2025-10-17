package repository

import (
	"context"
	"it-setup-service/domain"
)

type ProvisionRepository interface {
	Save(ctx context.Context, prov domain.Provision) (domain.Provision, error)
}
