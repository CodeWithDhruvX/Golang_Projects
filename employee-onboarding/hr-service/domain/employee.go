package domain

import "employee-onboarding/common/models"

type Employee = models.Employee // Use shared

type OnboardingRequest struct {
    Employee
}