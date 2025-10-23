```
## employee-onboarding/access-rights-service/access_test.go
```go
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

```

## employee-onboarding/access-rights-service/cmd/server/main.go
```go
package main



import (

	"access-rights-service/delivery/http"

	"access-rights-service/infrastructure/repository"

	"access-rights-service/usecase"

	"database/sql"

	"log"

	"os"



	"github.com/gin-gonic/gin"

	_ "github.com/go-sql-driver/mysql"

	"github.com/joho/godotenv"

)



func main() {

	_ = godotenv.Load("../.env")

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

```

## employee-onboarding/access-rights-service/delivery/http/handler.go
```go
package http



import (

	"access-rights-service/domain"

	"access-rights-service/usecase"

	"net/http"



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

```

## employee-onboarding/access-rights-service/domain/access.go
```go
package domain



type AccessGrant struct {

    ID         int      `json:"id"`

    EmployeeID int      `json:"employee_id"`

    Permissions []string `json:"permissions"`

}



type GrantRequest struct {

    EmployeeID int `json:"employee_id"`

}

```

## employee-onboarding/access-rights-service/infrastructure/repository/mysql_repository.go
```go
package repository



import (

	"access-rights-service/domain"

	"access-rights-service/repository"

	"context"

	"database/sql"

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

```

## employee-onboarding/access-rights-service/repository/interface.go
```go
package repository



import (

	"access-rights-service/domain"

	"context"

)



type AccessRepository interface {

	Save(ctx context.Context, grant domain.AccessGrant) (domain.AccessGrant, error)

}

```

## employee-onboarding/access-rights-service/usecase/access_usecase.go
```go
package usecase



import (

	"access-rights-service/domain"

	"access-rights-service/repository"

	"context"

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

```

## employee-onboarding/access-rights-service/usecase/interface.go
```go
package usecase



import (

	"access-rights-service/domain"

	"context"

)



type AccessUsecase interface {

	Grant(ctx context.Context, req domain.GrantRequest) (domain.AccessGrant, error)

}

```

## employee-onboarding/common/httpclient/client.go
```go
package httpclient



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

```

## employee-onboarding/common/models/employee.go
```go
package models



type Employee struct {

    ID      int    `json:"id"`

    Name    string `json:"name"`

    Email   string `json:"email"`

    Address string `json:"address"`

    Role    string `json:"role"`

}

```

## employee-onboarding/email-provisioner-service/cmd/server/main.go
```go
package main



import (

	"database/sql"

	"email-provisioner-service/delivery/http"

	"email-provisioner-service/infrastructure/email"

	"email-provisioner-service/infrastructure/repository"

	"email-provisioner-service/usecase"

	"log"

	"os"



	"github.com/gin-gonic/gin"

	_ "github.com/go-sql-driver/mysql"

	"github.com/joho/godotenv"

)



func main() {

	_ = godotenv.Load("../.env")

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

```

## employee-onboarding/email-provisioner-service/delivery/http/handler.go
```go
package http



import (

	"email-provisioner-service/domain"

	"email-provisioner-service/usecase"

	"net/http"



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

```

## employee-onboarding/email-provisioner-service/domain/email.go
```go
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

```

## employee-onboarding/email-provisioner-service/email_test.go
```go
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

```

## employee-onboarding/email-provisioner-service/infrastructure/email/interface.go
```go
package email



import "email-provisioner-service/domain"



type Sender interface {

	Send(req domain.SendRequest) error

}

```

## employee-onboarding/email-provisioner-service/infrastructure/email/mock_sender.go
```go
package email



import (

	"email-provisioner-service/domain"

	"fmt"

	"log"

)



type MockSender struct{}



func NewMockSender() Sender {

	return &MockSender{}

}



func (s *MockSender) Send(req domain.SendRequest) error {

	fmt.Printf("Mock email sent to %s for employee %d\n", req.Email, req.EmployeeID)

	log.Println("Email provisioned") // Simulate

	return nil

}

```

## employee-onboarding/email-provisioner-service/infrastructure/repository/mysql_repository.go
```go
package repository



import (

	"context"

	"database/sql"

	"email-provisioner-service/domain"

	"email-provisioner-service/repository"

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

```

## employee-onboarding/email-provisioner-service/repository/interface.go
```go
package repository



import (

	"context"

	"email-provisioner-service/domain"

)



type EmailRepository interface {

	Save(ctx context.Context, log domain.EmailLog) (domain.EmailLog, error)

}

```

## employee-onboarding/email-provisioner-service/usecase/email_usecase.go
```go
package usecase



import (

	"context"

	"email-provisioner-service/domain"

	"email-provisioner-service/infrastructure/email"

	"email-provisioner-service/repository"

)



type emailUsecase struct {

	repo   repository.EmailRepository

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

```

## employee-onboarding/email-provisioner-service/usecase/interface.go
```go
package usecase



import (

	"context"

	"email-provisioner-service/domain"

)



type EmailUsecase interface {

	Send(ctx context.Context, req domain.SendRequest) (domain.EmailLog, error)

}

```

## employee-onboarding/hr-service/cmd/server/main.go
```go
package main



import (

	"database/sql"

	"employee-onboarding/common/httpclient"

	"hr-service/delivery/http"

	infrastructure "hr-service/infrastructure/repository" // Imports the impl package (named "infrastructure")

	"hr-service/usecase"

	"log"

	"os"



	"github.com/gin-gonic/gin"

	_ "github.com/go-sql-driver/mysql"

	"github.com/joho/godotenv"

)



func main() {

	_ = godotenv.Load("../.env") // Load shared env

	dsn := os.Getenv("DB_DSN")

	port := os.Getenv("PORT")

	itURL := os.Getenv("IT_URL")

	emailURL := os.Getenv("EMAIL_URL")

	accessURL := os.Getenv("ACCESS_URL")

	log.Printf("DSN: %s", dsn)

	db, err := sql.Open("mysql", dsn)

	if err != nil {

		log.Fatal(err)

	}

	defer db.Close()



	empRepo := infrastructure.NewEmployeeMySQLRepository(db) // Changed: Use "infrastructure." prefix

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

```

## employee-onboarding/hr-service/delivery/http/handler.go
```go
package http



import (

	"hr-service/domain"

	"hr-service/usecase"

	"net/http"

	"strconv"



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

```

## employee-onboarding/hr-service/domain/employee.go
```go
package domain



import "employee-onboarding/common/models"



type Employee = models.Employee // Use shared



type OnboardingRequest struct {

    Employee

}
```

## employee-onboarding/hr-service/hr_test.go
```go
package main



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
```

## employee-onboarding/hr-service/infrastructure/http/orchestrator.go
```go
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

```

## employee-onboarding/hr-service/infrastructure/repository/mysql_repository.go
```go
package infrastructure



import (

	"context"

	"database/sql"

	"fmt"

	"hr-service/domain"

	"hr-service/repository" // Import the core interface

)



type employeeMySQLRepository struct {

	db *sql.DB

}



func NewEmployeeMySQLRepository(db *sql.DB) repository.EmployeeRepository {

	sqlQuery := `CREATE TABLE IF NOT EXISTS employees (

        id INT PRIMARY KEY AUTO_INCREMENT,

        name VARCHAR(255),

        email VARCHAR(255) UNIQUE,

        address VARCHAR(255),

        role VARCHAR(100)

    )`

	_, err := db.Exec(sqlQuery)

	if err != nil {

		fmt.Printf("Table creation error: %v\n", err)

	}

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

```

## employee-onboarding/hr-service/repository/interface.go
```go
package repository



import (

	"context"

	"hr-service/domain"

)



type EmployeeRepository interface {

	Save(ctx context.Context, emp domain.Employee) (domain.Employee, error)

	FindByID(ctx context.Context, id int) (domain.Employee, error)

}

```

## employee-onboarding/hr-service/usecase/employee_usecase.go
```go
package usecase



import (

	"context"

	"employee-onboarding/common/httpclient"

	"hr-service/domain"

	"hr-service/infrastructure/http"

	"hr-service/repository"

)



type employeeUsecase struct {

	repo         repository.EmployeeRepository

	itClient     *httpclient.Client

	emailClient  *httpclient.Client

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

```

## employee-onboarding/hr-service/usecase/interface.go
```go
package usecase



import (

	"context"

	"hr-service/domain"

)



type EmployeeUsecase interface {

	Onboard(ctx context.Context, req domain.OnboardingRequest) (domain.Employee, error)

	GetByID(ctx context.Context, id int) (domain.Employee, error)

}

```

## employee-onboarding/it-setup-service/cmd/server/main.go
```go
package main



import (

	"database/sql"

	"it-setup-service/delivery/http"

	"it-setup-service/infrastructure/repository"

	"it-setup-service/usecase"

	"log"

	"os"



	"github.com/gin-gonic/gin"

	_ "github.com/go-sql-driver/mysql"

	"github.com/joho/godotenv"

)



func main() {

	_ = godotenv.Load("../.env")

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

```

## employee-onboarding/it-setup-service/delivery/http/handler.go
```go
package http



import (

	"it-setup-service/domain"

	"it-setup-service/usecase"

	"net/http"



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

```

## employee-onboarding/it-setup-service/domain/provision.go
```go
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

```

## employee-onboarding/it-setup-service/infrastructure/repository/mysql_repository.go
```go
package repository



import (

	"context"

	"database/sql"

	"it-setup-service/domain"

	"it-setup-service/repository"

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

```

## employee-onboarding/it-setup-service/it_test.go
```go
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

```

## employee-onboarding/it-setup-service/repository/interface.go
```go
package repository



import (

	"context"

	"it-setup-service/domain"

)



type ProvisionRepository interface {

	Save(ctx context.Context, prov domain.Provision) (domain.Provision, error)

}

```

## employee-onboarding/it-setup-service/usecase/interface.go
```go
package usecase



import (

	"context"

	"it-setup-service/domain"

)



type ProvisionUsecase interface {

	Provision(ctx context.Context, req domain.ProvisionRequest) (domain.Provision, error)

}

```

## employee-onboarding/it-setup-service/usecase/provision_usecase.go
```go
package usecase



import (

	"context"

	"it-setup-service/domain"

	"it-setup-service/repository"

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

```

Here’s your **English version** of the same instruction set — with the same structure, tone, and detail level, but translated for a global/English-speaking audience 👇

---

## 🧠 Project Deep Explanation Template (Mentor Style)

### 🔍 What You’ll Do

You’ll provide the **project files** (via README, folder structure, or code snippets).

My task: To generate a **deep, file-by-file explanation** of how the entire project works — in simple, practical language with extra context.

---

### 🗂️ Explanation Structure

#### 1. **Project Overview**

* What’s the **main goal** of the project?
* What’s the **real-world use case** — who would actually use this?
* What **problem** does it solve, and **why is it useful**?

#### 2. **File-by-File Walkthrough**

For each file (in any language):

* **Role in the project** → What’s this file’s responsibility or purpose?
* **Key Highlights** → Important functions, classes, structs, interfaces, or core business logic.
* **Connections** → How this file interacts with others (imports, function calls, API requests, shared data, etc.).
* **Patterns & Principles** → If the file follows any design or architectural principles (e.g., Factory, Singleton, MVC, Clean Architecture), explain it.
* **Beginner-Friendly Analogy** → Simple, intuitive metaphor like:
  “Think of this file as the receptionist — it receives all the requests and routes them to the right department.”

#### 3. **Additional Insights**

* **Real-world usage examples:** What kind of practical scenarios this code would handle.
* **Testing ideas:** How you could test it — via unit tests, CLI commands, API endpoints, mock data, etc.
* **Possible improvements:** Best practices, optimizations, or future enhancements.
* **Performance / scalability notes:** Any aspects related to concurrency, caching, or database optimization.

---

### 💬 Tone & Style

* Explain like a **friendly mentor** teaching a junior developer.
* Don’t go into boring line-by-line breakdowns.
* Focus on **intuition, flow, and the bigger picture** — make it fun and easy to follow.
* Use **hooks and metaphors** to make concepts stick (like “This file is the brain,” or “This one’s the messenger between systems”).

---

### 🧩 Example Output Style

* **`main.go` / `app.js` / `index.py`** →
  “This is the entry point of the project — think of it as the front door. All user commands, API requests, or initial actions come here first, and then get passed to the right service or handler.”

* **`cache.go` / `cache.py` / `cache.js`** →
  “This acts like a helper that provides fast-access memory (cache). Imagine it as a small notepad where frequently used results are stored — so we don’t have to hit the database again and again.”

* **`db.go` / `database.py` / `models.js`** →
  “This file talks to the database. It handles queries or ORM operations and provides a structured way for the rest of the app to access and manage data.”

---

### 🎯 Final Goal

By the end of the explanation, a **junior developer** should be able to:

* Understand how the **whole project works** without reading every line of code.
* Know the **real-world purpose** of each part.
* See where improvements, optimizations, or extensions can be made.

---