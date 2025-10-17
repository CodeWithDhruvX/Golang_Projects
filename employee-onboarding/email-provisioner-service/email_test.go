package main

import (
    "context"
    "testing"
    "email-provisioner-service/domain"
    "email-provisioner-service/usecase"
    "github.com/stretchr/testify/assert"
)

func TestSend(t *testing.T) {
    // Placeholder mock
    mockRepo := // implement mock repo
    mockSender := // implement mock sender
    uc := usecase.NewEmailUsecase(mockRepo, mockSender)
    req := domain.SendRequest{EmployeeID: 1, Email: "test@example.com"}
    log, err := uc.Send(context.Background(), req)
    assert.NoError(t, err)
    assert.Equal(t, "Sent", log.Status)
}
