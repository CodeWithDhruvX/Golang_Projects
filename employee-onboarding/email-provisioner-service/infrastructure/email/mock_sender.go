package email

import (
	"email-provisioner-service/domain"
	"fmt"
	"log"
)

type MockSender struct{}

func NewMockSender() Sender {
	return &MockSender{}
}

func (s *MockSender) Send(req domain.SendRequest) error {
	fmt.Printf("Mock email sent to %s for employee %d\n", req.Email, req.EmployeeID)
	log.Println("Email provisioned") // Simulate
	return nil
}
