package main

import (
    "context"
    "testing"
    "domain"
    "usecase"
    "github.com/stretchr/testify/assert"
)

func TestGrant(t *testing.T) {
    // Placeholder mock
    mockRepo := // implement mock repo
    uc := usecase.NewAccessUsecase(mockRepo)
    req := domain.GrantRequest{EmployeeID: 1}
    grant, err := uc.Grant(context.Background(), req)
    assert.NoError(t, err)
    assert.Contains(t, grant.Permissions, "read")
}
