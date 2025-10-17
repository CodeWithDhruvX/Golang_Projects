package domain

type EmailLog struct {
    ID         int    `json:"id"`
    EmployeeID int    `json:"employee_id"`
    To         string `json:"to"`
    Subject    string `json:"subject"`
    Status     string `json:"status"`
}

type SendRequest struct {
    EmployeeID int    `json:"employee_id"`
    Email      string `json:"email"`
}
