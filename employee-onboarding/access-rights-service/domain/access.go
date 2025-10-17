package domain

type AccessGrant struct {
    ID         int      `json:"id"`
    EmployeeID int      `json:"employee_id"`
    Permissions []string `json:"permissions"`
}

type GrantRequest struct {
    EmployeeID int `json:"employee_id"`
}
