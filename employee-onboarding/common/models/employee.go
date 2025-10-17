package models

type Employee struct {
    ID      int    `json:"id"`
    Name    string `json:"name"`
    Email   string `json:"email"`
    Address string `json:"address"`
    Role    string `json:"role"`
}
