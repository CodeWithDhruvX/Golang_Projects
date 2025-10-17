package http

import (
	"context"
	"employee-onboarding/common/httpclient"
	"employee-onboarding/common/models"
	"net/http"
)

func CallITProvision(client *httpclient.Client, ctx context.Context, empID int) (bool, error) {
	payload := map[string]int{"employee_id": empID}
	resp, err := client.Post(ctx, "/api/v1/provision", payload)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK, nil
}

func CallEmailSend(client *httpclient.Client, ctx context.Context, emp models.Employee) (bool, error) {
	payload := map[string]interface{}{"employee_id": emp.ID, "email": emp.Email}
	resp, err := client.Post(ctx, "/api/v1/send", payload)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK, nil
}

func CallAccessGrant(client *httpclient.Client, ctx context.Context, empID int) (bool, error) {
	payload := map[string]int{"employee_id": empID}
	resp, err := client.Post(ctx, "/api/v1/grant", payload)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK, nil
}
