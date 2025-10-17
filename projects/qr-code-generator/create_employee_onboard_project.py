import os
import zipfile
from pathlib import Path

def create_directory(path: Path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def write_file(path: Path, content: str):
    """Write content to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def main():
    project_root = Path('employee-onboarding')
    create_directory(project_root)

    # Root files
    write_file(project_root / 'go.work', '''go 1.20

use (
    ./common
    ./hr-service
    ./it-setup-service
    ./email-provisioner-service
    ./access-rights-service
)
''')

    write_file(project_root / '.env', '''DB_DSN=root:password@tcp(127.0.0.1:3306)/onboarding?parseTime=true
PORT=8080
IT_URL=http://localhost:8081
EMAIL_URL=http://localhost:8082
ACCESS_URL=http://localhost:8083
''')

    # Common module setup
    common_dir = project_root / 'common'
    create_directory(common_dir / 'httpclient')
    create_directory(common_dir / 'models')

    write_file(common_dir / 'go.mod', '''module employee-onboarding/common

go 1.20
''')

    write_file(common_dir / 'httpclient' / 'client.go', '''package httpclient

import (
    "bytes"
    "context"
    "encoding/json"
    "net/http"
)

type Client struct {
    BaseURL string
}

func NewClient(baseURL string) *Client {
    return &Client{BaseURL: baseURL}
}

func (c *Client) Post(ctx context.Context, path string, payload interface{}) (*http.Response, error) {
    data, _ := json.Marshal(payload)
    req, err := http.NewRequestWithContext(ctx, "POST", c.BaseURL+path, bytes.NewBuffer(data))
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", "application/json")
    return http.DefaultClient.Do(req)
}
''')

    write_file(common_dir / 'models' / 'employee.go', '''package models

type Employee struct {
    ID      int    `json:"id"`
    Name    string `json:"name"`
    Email   string `json:"email"`
    Address string `json:"address"`
    Role    string `json:"role"`
}
''')

    # HR Service
    hr_dir = project_root / 'hr-service'
    create_directory(hr_dir / 'cmd' / 'server')
    create_directory(hr_dir / 'domain')
    create_directory(hr_dir / 'usecase')
    create_directory(hr_dir / 'repository')
    create_directory(hr_dir / 'infrastructure' / 'repository')
    create_directory(hr_dir / 'infrastructure' / 'http')
    create_directory(hr_dir / 'delivery' / 'http')

    write_file(hr_dir / 'go.mod', '''module hr-service

go 1.20

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/go-sql-driver/mysql v1.7.1
    github.com/joho/godotenv v1.5.1
    github.com/stretchr/testify v1.8.4
)

replace employee-onboarding/common => ../common
''')

    write_file(hr_dir / '.env.example', '''# Copy from root .env and adjust PORT=8080
''')

    write_file(hr_dir / 'domain' / 'employee.go', '''package domain

import "employee-onboarding/common/models"

type Employee = models.Employee // Use shared

type OnboardingRequest struct {
    Employee
}
''')

    write_file(hr_dir / 'usecase' / 'interface.go', '''package usecase

import (
    "context"
    "domain"
)

type EmployeeUsecase interface {
    Onboard(ctx context.Context, req domain.OnboardingRequest) (domain.Employee, error)
    GetByID(ctx context.Context, id int) (domain.Employee, error)
}
''')

    write_file(hr_dir / 'usecase' / 'employee_usecase.go', '''package usecase

import (
    "context"
    "employee-onboarding/common/httpclient"
    "employee-onboarding/common/models"
    "domain"
    "infrastructure/http"
    "repository"
)

type employeeUsecase struct {
    repo     repository.EmployeeRepository
    itClient *httpclient.Client
    emailClient *httpclient.Client
    accessClient *httpclient.Client
}

func NewEmployeeUsecase(repo repository.EmployeeRepository, itClient, emailClient, accessClient *httpclient.Client) EmployeeUsecase {
    return &employeeUsecase{repo: repo, itClient: itClient, emailClient: emailClient, accessClient: accessClient}
}

func (u *employeeUsecase) Onboard(ctx context.Context, req domain.OnboardingRequest) (domain.Employee, error) {
    emp := req.Employee
    saved, err := u.repo.Save(ctx, emp)
    if err != nil {
        return domain.Employee{}, err
    }
    // Orchestrate: Call other services
    _, _ = http.CallITProvision(u.itClient, ctx, saved.ID)
    _, _ = http.CallEmailSend(u.emailClient, ctx, saved)
    _, _ = http.CallAccessGrant(u.accessClient, ctx, saved.ID)
    return saved, nil
}

func (u *employeeUsecase) GetByID(ctx context.Context, id int) (domain.Employee, error) {
    return u.repo.FindByID(ctx, id)
}
''')

    write_file(hr_dir / 'repository' / 'interface.go', '''package repository

import (
    "context"
    "domain"
)

type EmployeeRepository interface {
    Save(ctx context.Context, emp domain.Employee) (domain.Employee, error)
    FindByID(ctx context.Context, id int) (domain.Employee, error)
}
''')

    write_file(hr_dir / 'infrastructure' / 'repository' / 'mysql_repository.go', '''package repository

import (
    "context"
    "database/sql"
    "domain"
    "fmt"
)

type employeeMySQLRepository struct {
    db *sql.DB
}

func NewEmployeeMySQLRepository(db *sql.DB) repository.EmployeeRepository {
    _, _ = db.Exec(`CREATE TABLE IF NOT EXISTS employees (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        address VARCHAR(255),
        role VARCHAR(100)
    )`)
    return &employeeMySQLRepository{db: db}
}

func (r *employeeMySQLRepository) Save(ctx context.Context, emp domain.Employee) (domain.Employee, error) {
    result, err := r.db.ExecContext(ctx, "INSERT INTO employees (name, email, address, role) VALUES (?, ?, ?, ?)",
        emp.Name, emp.Email, emp.Address, emp.Role)
    if err != nil {
        return domain.Employee{}, err
    }
    id, _ := result.LastInsertId()
    emp.ID = int(id)
    return emp, nil
}

func (r *employeeMySQLRepository) FindByID(ctx context.Context, id int) (domain.Employee, error) {
    var emp domain.Employee
    err := r.db.QueryRowContext(ctx, "SELECT id, name, email, address, role FROM employees WHERE id = ?", id).
        Scan(&emp.ID, &emp.Name, &emp.Email, &emp.Address, &emp.Role)
    return emp, err
}
''')

    write_file(hr_dir / 'infrastructure' / 'http' / 'orchestrator.go', '''package http

import (
    "context"
    "encoding/json"
    "net/http"
    "employee-onboarding/common/httpclient"
    "employee-onboarding/common/models"
    "domain"
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
''')

    write_file(hr_dir / 'delivery' / 'http' / 'handler.go', '''package http

import (
    "net/http"
    "strconv"
    "domain"
    "usecase"
    "github.com/gin-gonic/gin"
)

type employeeHandler struct {
    usecase usecase.EmployeeUsecase
}

func NewEmployeeHandler(usecase usecase.EmployeeUsecase) *employeeHandler {
    return &employeeHandler{usecase: usecase}
}

func (h *employeeHandler) Onboard(c *gin.Context) {
    var req domain.OnboardingRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    emp, err := h.usecase.Onboard(c.Request.Context(), req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, emp)
}

func (h *employeeHandler) GetByID(c *gin.Context) {
    idStr := c.Param("id")
    id, _ := strconv.Atoi(idStr)
    emp, err := h.usecase.GetByID(c.Request.Context(), id)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Not found"})
        return
    }
    c.JSON(http.StatusOK, emp)
}
''')

    write_file(hr_dir / 'cmd' / 'server' / 'main.go', '''package main

import (
    "database/sql"
    "log"
    "os"
    "employee-onboarding/common/httpclient"
    "delivery/http"
    "infrastructure/repository"
    "usecase"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    _ "github.com/go-sql-driver/mysql"
)

func main() {
    _ = godotenv.Load("../../.env") // Load shared env
    dsn := os.Getenv("DB_DSN")
    port := os.Getenv("PORT")
    itURL := os.Getenv("IT_URL")
    emailURL := os.Getenv("EMAIL_URL")
    accessURL := os.Getenv("ACCESS_URL")

    db, err := sql.Open("mysql", dsn)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    empRepo := repository.NewEmployeeMySQLRepository(db)
    itClient := httpclient.NewClient(itURL)
    emailClient := httpclient.NewClient(emailURL)
    accessClient := httpclient.NewClient(accessURL)
    empUsecase := usecase.NewEmployeeUsecase(empRepo, itClient, emailClient, accessClient)
    handler := http.NewEmployeeHandler(empUsecase)

    r := gin.Default()
    v1 := r.Group("/api/v1")
    v1.POST("/onboard", handler.Onboard)
    v1.GET("/employee/:id", handler.GetByID)

    r.Run(":" + port)
}
''')

    write_file(hr_dir / 'hr_test.go', '''package main

import (
    "context"
    "testing"
    "domain"
    "usecase"
    "github.com/stretchr/testify/assert"
)

func TestOnboard(t *testing.T) {
    // Placeholder mock; expand with testify/mock
    mockRepo := // implement mock repo
    itClient := // mock
    emailClient := // mock
    accessClient := // mock
    uc := usecase.NewEmployeeUsecase(mockRepo, itClient, emailClient, accessClient)
    req := domain.OnboardingRequest{Employee: domain.Employee{Name: "Test", Email: "test@example.com", Address: "Test Addr", Role: "Dev"}}
    emp, err := uc.Onboard(context.Background(), req)
    assert.NoError(t, err)
    assert.Equal(t, "Test", emp.Name)
}
''')

    # IT Setup Service (updated imports)
    it_dir = project_root / 'it-setup-service'
    create_directory(it_dir / 'cmd' / 'server')
    create_directory(it_dir / 'domain')
    create_directory(it_dir / 'usecase')
    create_directory(it_dir / 'repository')
    create_directory(it_dir / 'infrastructure' / 'repository')
    create_directory(it_dir / 'delivery' / 'http')

    write_file(it_dir / 'go.mod', '''module it-setup-service

go 1.20

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/go-sql-driver/mysql v1.7.1
    github.com/joho/godotenv v1.5.1
    github.com/stretchr/testify v1.8.4
)

replace employee-onboarding/common => ../common
''')

    write_file(it_dir / '.env.example', '''# Copy from root .env and adjust PORT=8081
''')

    write_file(it_dir / 'domain' / 'provision.go', '''package domain

type Provision struct {
    ID         int    `json:"id"`
    EmployeeID int    `json:"employee_id"`
    Device     string `json:"device"`
    Status     string `json:"status"`
}

type ProvisionRequest struct {
    EmployeeID int `json:"employee_id"`
}
''')

    write_file(it_dir / 'usecase' / 'interface.go', '''package usecase

import (
    "context"
    "domain"
)

type ProvisionUsecase interface {
    Provision(ctx context.Context, req domain.ProvisionRequest) (domain.Provision, error)
}
''')

    write_file(it_dir / 'usecase' / 'provision_usecase.go', '''package usecase

import (
    "context"
    "domain"
    "repository"
)

type provisionUsecase struct {
    repo repository.ProvisionRepository
}

func NewProvisionUsecase(repo repository.ProvisionRepository) ProvisionUsecase {
    return &provisionUsecase{repo: repo}
}

func (u *provisionUsecase) Provision(ctx context.Context, req domain.ProvisionRequest) (domain.Provision, error) {
    prov := domain.Provision{EmployeeID: req.EmployeeID, Device: "Laptop", Status: "Provisioned"}
    return u.repo.Save(ctx, prov)
}
''')

    write_file(it_dir / 'repository' / 'interface.go', '''package repository

import (
    "context"
    "domain"
)

type ProvisionRepository interface {
    Save(ctx context.Context, prov domain.Provision) (domain.Provision, error)
}
''')

    write_file(it_dir / 'infrastructure' / 'repository' / 'mysql_repository.go', '''package repository

import (
    "context"
    "database/sql"
    "domain"
)

type provisionMySQLRepository struct {
    db *sql.DB
}

func NewProvisionMySQLRepository(db *sql.DB) repository.ProvisionRepository {
    _, _ = db.Exec(`CREATE TABLE IF NOT EXISTS it_provisions (
        id INT PRIMARY KEY AUTO_INCREMENT,
        employee_id INT,
        device VARCHAR(255),
        status VARCHAR(100)
    )`)
    return &provisionMySQLRepository{db: db}
}

func (r *provisionMySQLRepository) Save(ctx context.Context, prov domain.Provision) (domain.Provision, error) {
    result, err := r.db.ExecContext(ctx, "INSERT INTO it_provisions (employee_id, device, status) VALUES (?, ?, ?)",
        prov.EmployeeID, prov.Device, prov.Status)
    if err != nil {
        return domain.Provision{}, err
    }
    id, _ := result.LastInsertId()
    prov.ID = int(id)
    return prov, nil
}
''')

    write_file(it_dir / 'delivery' / 'http' / 'handler.go', '''package http

import (
    "net/http"
    "domain"
    "usecase"
    "github.com/gin-gonic/gin"
)

type provisionHandler struct {
    usecase usecase.ProvisionUsecase
}

func NewProvisionHandler(usecase usecase.ProvisionUsecase) *provisionHandler {
    return &provisionHandler{usecase: usecase}
}

func (h *provisionHandler) Provision(c *gin.Context) {
    var req domain.ProvisionRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    prov, err := h.usecase.Provision(c.Request.Context(), req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, prov)
}
''')

    write_file(it_dir / 'cmd' / 'server' / 'main.go', '''package main

import (
    "database/sql"
    "log"
    "os"
    "delivery/http"
    "infrastructure/repository"
    "usecase"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    _ "github.com/go-sql-driver/mysql"
)

func main() {
    _ = godotenv.Load("../../.env")
    dsn := os.Getenv("DB_DSN")
    port := "8081"

    db, err := sql.Open("mysql", dsn)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    provRepo := repository.NewProvisionMySQLRepository(db)
    provUsecase := usecase.NewProvisionUsecase(provRepo)
    handler := http.NewProvisionHandler(provUsecase)

    r := gin.Default()
    v1 := r.Group("/api/v1")
    v1.POST("/provision", handler.Provision)

    r.Run(":" + port)
}
''')

    write_file(it_dir / 'it_test.go', '''package main

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
''')

    # Email Provisioner Service (updated imports)
    email_dir = project_root / 'email-provisioner-service'
    create_directory(email_dir / 'cmd' / 'server')
    create_directory(email_dir / 'domain')
    create_directory(email_dir / 'usecase')
    create_directory(email_dir / 'repository')
    create_directory(email_dir / 'infrastructure' / 'repository')
    create_directory(email_dir / 'infrastructure' / 'email')
    create_directory(email_dir / 'delivery' / 'http')

    write_file(email_dir / 'go.mod', '''module email-provisioner-service

go 1.20

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/go-sql-driver/mysql v1.7.1
    github.com/joho/godotenv v1.5.1
    github.com/stretchr/testify v1.8.4
)

replace employee-onboarding/common => ../common
''')

    write_file(email_dir / '.env.example', '''# Copy from root .env and adjust PORT=8082
''')

    write_file(email_dir / 'domain' / 'email.go', '''package domain

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
''')

    write_file(email_dir / 'usecase' / 'interface.go', '''package usecase

import (
    "context"
    "domain"
)

type EmailUsecase interface {
    Send(ctx context.Context, req domain.SendRequest) (domain.EmailLog, error)
}
''')

    write_file(email_dir / 'usecase' / 'email_usecase.go', '''package usecase

import (
    "context"
    "domain"
    "infrastructure/email"
    "repository"
)

type emailUsecase struct {
    repo  repository.EmailRepository
    sender email.Sender
}

func NewEmailUsecase(repo repository.EmailRepository, sender email.Sender) EmailUsecase {
    return &emailUsecase{repo: repo, sender: sender}
}

func (u *emailUsecase) Send(ctx context.Context, req domain.SendRequest) (domain.EmailLog, error) {
    err := u.sender.Send(req)
    if err != nil {
        return domain.EmailLog{}, err
    }
    log := domain.EmailLog{EmployeeID: req.EmployeeID, To: req.Email, Subject: "Welcome", Status: "Sent"}
    return u.repo.Save(ctx, log)
}
''')

    write_file(email_dir / 'repository' / 'interface.go', '''package repository

import (
    "context"
    "domain"
)

type EmailRepository interface {
    Save(ctx context.Context, log domain.EmailLog) (domain.EmailLog, error)
}
''')

    write_file(email_dir / 'infrastructure' / 'repository' / 'mysql_repository.go', '''package repository

import (
    "context"
    "database/sql"
    "domain"
)

type emailMySQLRepository struct {
    db *sql.DB
}

func NewEmailMySQLRepository(db *sql.DB) repository.EmailRepository {
    _, _ = db.Exec(`CREATE TABLE IF NOT EXISTS email_logs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        employee_id INT,
        to_email VARCHAR(255),
        subject VARCHAR(255),
        status VARCHAR(100)
    )`)
    return &emailMySQLRepository{db: db}
}

func (r *emailMySQLRepository) Save(ctx context.Context, log domain.EmailLog) (domain.EmailLog, error) {
    result, err := r.db.ExecContext(ctx, "INSERT INTO email_logs (employee_id, to_email, subject, status) VALUES (?, ?, ?, ?)",
        log.EmployeeID, log.To, log.Subject, log.Status)
    if err != nil {
        return domain.EmailLog{}, err
    }
    id, _ := result.LastInsertId()
    log.ID = int(id)
    return log, nil
}
''')

    write_file(email_dir / 'infrastructure' / 'email' / 'interface.go', '''package email

import "domain"

type Sender interface {
    Send(req domain.SendRequest) error
}
''')

    write_file(email_dir / 'infrastructure' / 'email' / 'mock_sender.go', '''package email

import (
    "fmt"
    "log"
    "domain"
)

type MockSender struct{}

func NewMockSender() Sender {
    return &MockSender{}
}

func (s *MockSender) Send(req domain.SendRequest) error {
    fmt.Printf("Mock email sent to %s for employee %d\\n", req.Email, req.EmployeeID)
    log.Println("Email provisioned") // Simulate
    return nil
}
''')

    write_file(email_dir / 'delivery' / 'http' / 'handler.go', '''package http

import (
    "net/http"
    "domain"
    "usecase"
    "github.com/gin-gonic/gin"
)

type emailHandler struct {
    usecase usecase.EmailUsecase
}

func NewEmailHandler(usecase usecase.EmailUsecase) *emailHandler {
    return &emailHandler{usecase: usecase}
}

func (h *emailHandler) Send(c *gin.Context) {
    var req domain.SendRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    log, err := h.usecase.Send(c.Request.Context(), req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, log)
}
''')

    write_file(email_dir / 'cmd' / 'server' / 'main.go', '''package main

import (
    "database/sql"
    "log"
    "os"
    "delivery/http"
    "infrastructure/email"
    "infrastructure/repository"
    "usecase"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    _ "github.com/go-sql-driver/mysql"
)

func main() {
    _ = godotenv.Load("../../.env")
    dsn := os.Getenv("DB_DSN")
    port := "8082"

    db, err := sql.Open("mysql", dsn)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    emailRepo := repository.NewEmailMySQLRepository(db)
    sender := email.NewMockSender()
    emailUsecase := usecase.NewEmailUsecase(emailRepo, sender)
    handler := http.NewEmailHandler(emailUsecase)

    r := gin.Default()
    v1 := r.Group("/api/v1")
    v1.POST("/send", handler.Send)

    r.Run(":" + port)
}
''')

    write_file(email_dir / 'email_test.go', '''package main

import (
    "context"
    "testing"
    "domain"
    "usecase"
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
''')

    # Access Rights Service (updated imports)
    access_dir = project_root / 'access-rights-service'
    create_directory(access_dir / 'cmd' / 'server')
    create_directory(access_dir / 'domain')
    create_directory(access_dir / 'usecase')
    create_directory(access_dir / 'repository')
    create_directory(access_dir / 'infrastructure' / 'repository')
    create_directory(access_dir / 'delivery' / 'http')

    write_file(access_dir / 'go.mod', '''module access-rights-service

go 1.20

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/go-sql-driver/mysql v1.7.1
    github.com/joho/godotenv v1.5.1
    github.com/stretchr/testify v1.8.4
)

replace employee-onboarding/common => ../common
''')

    write_file(access_dir / '.env.example', '''# Copy from root .env and adjust PORT=8083
''')

    write_file(access_dir / 'domain' / 'access.go', '''package domain

type AccessGrant struct {
    ID         int      `json:"id"`
    EmployeeID int      `json:"employee_id"`
    Permissions []string `json:"permissions"`
}

type GrantRequest struct {
    EmployeeID int `json:"employee_id"`
}
''')

    write_file(access_dir / 'usecase' / 'interface.go', '''package usecase

import (
    "context"
    "domain"
)

type AccessUsecase interface {
    Grant(ctx context.Context, req domain.GrantRequest) (domain.AccessGrant, error)
}
''')

    write_file(access_dir / 'usecase' / 'access_usecase.go', '''package usecase

import (
    "context"
    "domain"
    "repository"
)

type accessUsecase struct {
    repo repository.AccessRepository
}

func NewAccessUsecase(repo repository.AccessRepository) AccessUsecase {
    return &accessUsecase{repo: repo}
}

func (u *accessUsecase) Grant(ctx context.Context, req domain.GrantRequest) (domain.AccessGrant, error) {
    grant := domain.AccessGrant{EmployeeID: req.EmployeeID, Permissions: []string{"read", "write"}}
    return u.repo.Save(ctx, grant)
}
''')

    write_file(access_dir / 'repository' / 'interface.go', '''package repository

import (
    "context"
    "domain"
)

type AccessRepository interface {
    Save(ctx context.Context, grant domain.AccessGrant) (domain.AccessGrant, error)
}
''')

    write_file(access_dir / 'infrastructure' / 'repository' / 'mysql_repository.go', '''package repository

import (
    "context"
    "database/sql"
    "domain"
    "encoding/json"
)

type accessMySQLRepository struct {
    db *sql.DB
}

func NewAccessMySQLRepository(db *sql.DB) repository.AccessRepository {
    _, _ = db.Exec(`CREATE TABLE IF NOT EXISTS access_grants (
        id INT PRIMARY KEY AUTO_INCREMENT,
        employee_id INT,
        permissions JSON
    )`)
    return &accessMySQLRepository{db: db}
}

func (r *accessMySQLRepository) Save(ctx context.Context, grant domain.AccessGrant) (domain.AccessGrant, error) {
    permsJSON, _ := json.Marshal(grant.Permissions)
    result, err := r.db.ExecContext(ctx, "INSERT INTO access_grants (employee_id, permissions) VALUES (?, ?)",
        grant.EmployeeID, string(permsJSON))
    if err != nil {
        return domain.AccessGrant{}, err
    }
    id, _ := result.LastInsertId()
    grant.ID = int(id)
    return grant, nil
}
''')

    write_file(access_dir / 'delivery' / 'http' / 'handler.go', '''package http

import (
    "net/http"
    "domain"
    "usecase"
    "github.com/gin-gonic/gin"
)

type accessHandler struct {
    usecase usecase.AccessUsecase
}

func NewAccessHandler(usecase usecase.AccessUsecase) *accessHandler {
    return &accessHandler{usecase: usecase}
}

func (h *accessHandler) Grant(c *gin.Context) {
    var req domain.GrantRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    grant, err := h.usecase.Grant(c.Request.Context(), req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, grant)
}
''')

    write_file(access_dir / 'cmd' / 'server' / 'main.go', '''package main

import (
    "database/sql"
    "log"
    "os"
    "delivery/http"
    "infrastructure/repository"
    "usecase"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    _ "github.com/go-sql-driver/mysql"
)

func main() {
    _ = godotenv.Load("../../.env")
    dsn := os.Getenv("DB_DSN")
    port := "8083"

    db, err := sql.Open("mysql", dsn)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    accessRepo := repository.NewAccessMySQLRepository(db)
    accessUsecase := usecase.NewAccessUsecase(accessRepo)
    handler := http.NewAccessHandler(accessUsecase)

    r := gin.Default()
    v1 := r.Group("/api/v1")
    v1.POST("/grant", handler.Grant)

    r.Run(":" + port)
}
''')

    write_file(access_dir / 'access_test.go', '''package main

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
''')

    # Zip the project
    zip_path = Path('employee-onboarding.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_root):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project_root)
                zipf.write(file_path, arcname)

    print(f"Updated project created in {project_root} and zipped as {zip_path}")
    print("Run 'go work sync' in root after unzipping for module setup.")

if __name__ == "__main__":
    main()
