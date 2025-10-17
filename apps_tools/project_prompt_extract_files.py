import os
import zipfile

# === Base project directory ===
base_dir = "employee-onboard"

# === Folder structure ===
folders = [
    "cmd/hr",
    "cmd/itsetup",
    "cmd/email",
    "cmd/access",
    "internal/common",
    "internal/hr/domain",
    "internal/hr/repository",
    "internal/hr/service",
    "internal/hr/transport",
    "internal/itsetup/transport",
    "internal/email",
    "internal/access",
    "data"
]

# === Files and their contents ===
files = {
    "cmd/hr/main.go": """package main
import (
    "fmt"
    "log"
    "net/http"
    "employee-onboard/internal/hr/transport"
)
func main() {
    fmt.Println("HR service running on :8001")
    http.HandleFunc("/onboard", transport.OnboardHandler)
    log.Fatal(http.ListenAndServe(":8001", nil))
}
""",

    "cmd/itsetup/main.go": """package main
import (
    "fmt"
    "log"
    "net/http"
    "employee-onboard/internal/itsetup/transport"
)
func main() {
    fmt.Println("IT Setup service running on :8002")
    http.HandleFunc("/provision", transport.ProvisionHandler)
    log.Fatal(http.ListenAndServe(":8002", nil))
}
""",

    "cmd/email/main.go": """package main
import (
    "fmt"
    "log"
    "net/http"
)
func main() {
    fmt.Println("Email service running on :8003")
    http.HandleFunc("/send", SendEmailHandler)
    log.Fatal(http.ListenAndServe(":8003", nil))
}
""",

    "cmd/email/handlers.go": """package main
import (
    "encoding/json"
    "fmt"
    "net/http"
)
type EmailRequest struct {
    To string `json:"to"`
    Subject string `json:"subject"`
    Body string `json:"body"`
}
func SendEmailHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
        return
    }
    var req EmailRequest
    json.NewDecoder(r.Body).Decode(&req)
    fmt.Fprintf(w, "Email sent to %s with subject: %s", req.To, req.Subject)
}
""",

    "cmd/access/main.go": """package main
import (
    "fmt"
    "log"
    "net/http"
)
func main() {
    fmt.Println("Access service running on :8004")
    http.HandleFunc("/grant", GrantAccessHandler)
    log.Fatal(http.ListenAndServe(":8004", nil))
}
""",

    "cmd/access/handler.go": """package main
import (
    "encoding/json"
    "fmt"
    "net/http"
)
type AccessRequest struct {
    EmployeeID string `json:"employee_id"`
    Role string `json:"role"`
}
func GrantAccessHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
        return
    }
    var req AccessRequest
    json.NewDecoder(r.Body).Decode(&req)
    fmt.Fprintf(w, "Access granted to employee %s as %s", req.EmployeeID, req.Role)
}
""",

    "internal/common/types.go": """package common
type Employee struct {
    ID string `json:"id"`
    Name string `json:"name"`
    Department string `json:"department"`
    Email string `json:"email"`
}
""",

    "internal/hr/domain/employee.go": """package domain
type Employee struct {
    ID string
    Name string
    Department string
    Email string
}
""",

    "internal/hr/repository/file_repo.go": """package repository
import (
    "encoding/json"
    "os"
    "employee-onboard/internal/hr/domain"
)
type FileRepo struct {
    Path string
}
func (r *FileRepo) Save(emp domain.Employee) error {
    file, _ := os.OpenFile(r.Path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
    defer file.Close()
    data, _ := json.Marshal(emp)
    file.Write(append(data, '\\n'))
    return nil
}
""",

    "internal/hr/service/onboarding.go": """package service
import (
    "employee-onboard/internal/hr/domain"
    "employee-onboard/internal/hr/repository"
)
type OnboardingService struct {
    Repo *repository.FileRepo
}
func (s *OnboardingService) OnboardEmployee(emp domain.Employee) error {
    return s.Repo.Save(emp)
}
""",

    "internal/hr/transport/http.go": """package transport
import (
    "encoding/json"
    "fmt"
    "net/http"
    "employee-onboard/internal/hr/domain"
    "employee-onboard/internal/hr/repository"
    "employee-onboard/internal/hr/service"
)
func OnboardHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
        return
    }
    var emp domain.Employee
    json.NewDecoder(r.Body).Decode(&emp)
    repo := &repository.FileRepo{Path: "data/hr.json"}
    srv := service.OnboardingService{Repo: repo}
    srv.OnboardEmployee(emp)
    fmt.Fprintf(w, "Employee onboarded: %s", emp.Name)
}
""",

    "internal/itsetup/transport/provision.go": """package transport
import (
    "encoding/json"
    "fmt"
    "net/http"
)
type ITRequest struct {
    EmployeeID string `json:"employee_id"`
    Device string `json:"device"`
}
func ProvisionHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
        return
    }
    var req ITRequest
    json.NewDecoder(r.Body).Decode(&req)
    fmt.Fprintf(w, "Provisioned %s for employee %s", req.Device, req.EmployeeID)
}
""",

    "data/hr.json": "",
    "data/itsetup.json": "",
    "data/email.json": "",
    "data/access.json": "",
    ".env.example": "HR_PORT=8001\\nIT_PORT=8002\\nEMAIL_PORT=8003\\nACCESS_PORT=8004\\n",
    "go.mod": "module employee-onboard\\ngo 1.21\\n",
    "README.md": "# Employee Onboarding System (Clean Architecture)\\n"
}

# === Create all folders ===
for folder in folders:
    os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

# === Write all files ===
for filepath, content in files.items():
    with open(os.path.join(base_dir, filepath), "w") as f:
        f.write(content)

# === Create ZIP ===
zip_path = "employee-onboard-final.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files_in_dir in os.walk(base_dir):
        for file in files_in_dir:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, base_dir)
            zipf.write(abs_path, rel_path)

print(f"✅ Project generated and zipped successfully: {zip_path}")
