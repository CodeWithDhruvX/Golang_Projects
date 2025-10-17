package email

import "email-provisioner-service/domain"

type Sender interface {
	Send(req domain.SendRequest) error
}
