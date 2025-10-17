package domain

type Provision struct {
    ID         int    `json:"id"`
    EmployeeID int    `json:"employee_id"`
    Device     string `json:"device"`
    Status     string `json:"status"`
}

type ProvisionRequest struct {
    EmployeeID int `json:"employee_id"`
}
