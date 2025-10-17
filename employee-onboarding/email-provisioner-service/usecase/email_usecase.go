package usecase

import (
	"context"
	"email-provisioner-service/domain"
	"email-provisioner-service/infrastructure/email"
	"email-provisioner-service/repository"
)

type emailUsecase struct {
	repo   repository.EmailRepository
	sender email.Sender
}

func NewEmailUsecase(repo repository.EmailRepository, sender email.Sender) EmailUsecase {
	return &emailUsecase{repo: repo, sender: sender}
}

func (u *emailUsecase) Send(ctx context.Context, req domain.SendRequest) (domain.EmailLog, error) {
	err := u.sender.Send(req)
	if err != nil {
		return domain.EmailLog{}, err
	}
	log := domain.EmailLog{EmployeeID: req.EmployeeID, To: req.Email, Subject: "Welcome", Status: "Sent"}
	return u.repo.Save(ctx, log)
}
