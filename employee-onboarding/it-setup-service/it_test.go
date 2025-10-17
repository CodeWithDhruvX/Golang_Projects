package main

import (
    "context"
    "testing"
    "domain"
    "usecase"
    "github.com/stretchr/testify/assert"
)

func TestProvision(t *testing.T) {
    // Placeholder mock
    mockRepo := // implement mock repo
    uc := usecase.NewProvisionUsecase(mockRepo)
    req := domain.ProvisionRequest{EmployeeID: 1}
    prov, err := uc.Provision(context.Background(), req)
    assert.NoError(t, err)
    assert.Equal(t, "Laptop", prov.Device)
}
