package usecase

import (
	"context"
	"email-provisioner-service/domain"
)

type EmailUsecase interface {
	Send(ctx context.Context, req domain.SendRequest) (domain.EmailLog, error)
}
