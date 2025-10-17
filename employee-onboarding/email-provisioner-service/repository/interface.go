package repository

import (
	"context"
	"email-provisioner-service/domain"
)

type EmailRepository interface {
	Save(ctx context.Context, log domain.EmailLog) (domain.EmailLog, error)
}
