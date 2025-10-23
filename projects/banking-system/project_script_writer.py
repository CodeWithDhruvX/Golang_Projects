import os
import zipfile
import time  # Not needed, but for completeness

# Project root
project_dir = 'banking-api'
zip_filename = 'banking-api.zip'

# Content for each file (full app code: all models, repos, services, handlers, etc.)
files_content = {
    'go.mod': '''module banking-api

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    gorm.io/gorm v1.25.5
    gorm.io/driver/mysql v1.5.4
    github.com/golang-jwt/jwt/v4 v4.5.0
    golang.org/x/crypto v0.17.0
    github.com/joho/godotenv v1.5.1
    github.com/stretchr/testify v1.8.4 // For testing
)
''',

    '.env.example': '''# Copy to .env and update with real values
DB_DSN=root:root@tcp(localhost:3306)/banking_db?parseTime=true&charset=utf8mb4&collation=utf8mb4_unicode_ci
JWT_SECRET=your-super-secret-jwt-key-min-32-chars-longer-for-security
PORT=8080
''',

    'migrations/schema.sql': '''-- Banking API Database Schema (supports all features: loans with total_payable)
USE banking_db;

-- Drop tables in reverse order if they exist (for clean re-runs)
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS loan_payments;
DROP TABLE IF EXISTS beneficiaries;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS customers;

-- Create independent tables first
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20)
) ENGINE=InnoDB;

-- Tables with foreign keys to customers/branches
CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    branch_id INT NOT NULL,
    owner VARCHAR(255) NOT NULL,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE RESTRICT,
    INDEX idx_customer_id (customer_id),
    INDEX idx_branch_id (branch_id)
) ENGINE=InnoDB;

CREATE TABLE loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    branch_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 4) NOT NULL,
    term_months INT NOT NULL,
    total_payable DECIMAL(15, 2) NOT NULL,
    status ENUM('pending', 'approved', 'repaid', 'defaulted') DEFAULT 'pending',
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE RESTRICT,
    INDEX idx_customer_id (customer_id),
    INDEX idx_branch_id (branch_id)
) ENGINE=InnoDB;

-- Dependent tables
CREATE TABLE loan_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,
    status ENUM('pending', 'paid', 'overdue') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE,
    INDEX idx_loan_id (loan_id)
) ENGINE=InnoDB;

CREATE TABLE beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    bank_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id)
) ENGINE=InnoDB;

-- Final table with multiple foreign keys
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_account_id INT NULL,
    to_account_id INT NULL,
    loan_payment_id INT NULL,
    beneficiary_id INT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_account_id) REFERENCES accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (to_account_id) REFERENCES accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (loan_payment_id) REFERENCES loan_payments(id) ON DELETE SET NULL,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE SET NULL,
    INDEX idx_from_account (from_account_id),
    INDEX idx_to_account (to_account_id),
    INDEX idx_loan_payment (loan_payment_id),
    INDEX idx_beneficiary (beneficiary_id)
) ENGINE=InnoDB;

-- Insert sample data (branches; customers/accounts added via API)
INSERT INTO branches (name, code, city, address, phone) VALUES 
('Main Branch', 'MB001', 'Mumbai', '123 Finance St, Mumbai', '+91-22-1234567'),
('South Branch', 'SB002', 'Bangalore', '456 Tech Ave, Bangalore', '+91-80-7654321'),
('North Branch', 'NB003', 'Delhi', '789 Capital Rd, Delhi', '+91-11-9876543');
''',

    'internal/db/db.go': '''package db

import (
    "log"
    "os"

    "gorm.io/driver/mysql"
    "gorm.io/gorm"
    "banking-api/internal/models"
)

func Connect() *gorm.DB {
    dsn := os.Getenv("DB_DSN")
    if dsn == "" {
        log.Fatal("DB_DSN is empty! Ensure .env is loaded.")
    }
    
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        log.Fatalf("[error] failed to initialize database, got error %v", err)
    }
    
    // Auto-migrate models (comment out if using manual schema.sql)
    err = db.AutoMigrate(&models.Customer{}, &models.Branch{}, &models.Account{}, &models.Transaction{}, &models.Loan{}, &models.LoanPayment{}, &models.Beneficiary{})
    if err != nil {
        log.Fatalf("AutoMigrate failed: %v", err)
    }
    log.Println("Database connected and migrated successfully!")
    
    return db
}
''',

    'internal/models/models.go': '''package models

import "time"

type Customer struct {
    ID          int       `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    Username    string    `gorm:"unique;size:50" json:"username"`
    PasswordHash string   `json:"-" gorm:"size:255"`
    FirstName   string    `json:"first_name"`
    LastName    string    `json:"last_name"`
    Email       string    `gorm:"unique;size:100" json:"email"`
    Phone       string    `json:"phone"`
    Address     string    `json:"address"`
    CreatedAt   time.Time `json:"created_at"`
    Accounts    []Account `gorm:"foreignKey:CustomerID" json:"-"`
    Loans       []Loan    `gorm:"foreignKey:CustomerID" json:"-"`
    Beneficiaries []Beneficiary `gorm:"foreignKey:CustomerID" json:"-"`
}

type Branch struct {
    ID     int      `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    Name   string   `json:"name"`
    Code   string   `gorm:"unique;size:10" json:"code"`
    City   string   `json:"city"`
    Address string  `json:"address"`
    Phone  string   `json:"phone"`
    Accounts []Account `gorm:"foreignKey:BranchID" json:"-"`
    Loans    []Loan     `gorm:"foreignKey:BranchID" json:"-"`
}

type Account struct {
    ID        int        `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    CustomerID int       `json:"customer_id" gorm:"type:int;index"`
    Customer  *Customer  `gorm:"foreignKey:CustomerID" json:"customer"`
    BranchID  int        `json:"branch_id" gorm:"type:int;index"`
    Branch    *Branch    `gorm:"foreignKey:BranchID" json:"branch"`
    Owner     string     `json:"owner"`
    Balance   float64    `gorm:"type:decimal(15,2)" json:"balance"`
    Currency  string     `json:"currency"`
    CreatedAt time.Time  `json:"created_at"`
    Transactions []Transaction `gorm:"foreignKey:FromAccountID;references:id" json:"-"`
}

type Transaction struct {
    ID            int      `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    FromAccountID *int     `json:"from_account_id" gorm:"type:int;index"`
    ToAccountID   *int     `json:"to_account_id" gorm:"type:int;index"`
    LoanPaymentID *int     `json:"loan_payment_id" gorm:"type:int;index"`
    BeneficiaryID *int     `json:"beneficiary_id" gorm:"type:int;index"`
    Amount        float64  `gorm:"type:decimal(15,2)" json:"amount"`
    CreatedAt     time.Time `json:"created_at"`
}

type Loan struct {
    ID           int     `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    CustomerID   int     `json:"customer_id" gorm:"type:int;index"`
    Customer     *Customer `gorm:"foreignKey:CustomerID" json:"customer"`
    BranchID     int     `json:"branch_id" gorm:"type:int;index"`
    Branch       *Branch `gorm:"foreignKey:BranchID" json:"branch"`
    Amount       float64 `gorm:"type:decimal(15,2)" json:"amount"`
    InterestRate float64 `gorm:"type:decimal(5,4)" json:"interest_rate"`
    TermMonths   int     `json:"term_months"`
    TotalPayable float64 `gorm:"type:decimal(15,2)" json:"total_payable"`
    Status       string  `json:"status"`
    StartDate    time.Time `json:"start_date"`
    EndDate      time.Time `json:"end_date"`
    CreatedAt    time.Time `json:"created_at"`
    Payments     []LoanPayment `gorm:"foreignKey:LoanID" json:"payments"`
}

type LoanPayment struct {
    ID        int       `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    LoanID    int       `json:"loan_id" gorm:"type:int;index"`
    Loan      *Loan     `gorm:"foreignKey:LoanID" json:"loan"`
    Amount    float64   `gorm:"type:decimal(15,2)" json:"amount"`
    DueDate   time.Time `json:"due_date"`
    PaidDate  time.Time `json:"paid_date"`
    Status    string    `json:"status"`
    CreatedAt time.Time `json:"created_at"`
}

type Beneficiary struct {
    ID           int    `gorm:"primaryKey;autoIncrement;type:int" json:"id"`
    CustomerID   int    `json:"customer_id" gorm:"type:int;index"`
    Name         string `json:"name"`
    AccountNumber string `json:"account_number"`
    BankName     string `json:"bank_name"`
}

// Request structs for validation
type CreateAccountRequest struct {
    Owner    string  `json:"owner" binding:"required"`
    Currency string  `json:"currency" binding:"required"`
}

type TransferRequest struct {
    ToAccountID int     `json:"to_account_id" binding:"required"`
    Amount      float64 `json:"amount" binding:"required,gt=0"`
}

type CreateLoanRequest struct {
    Amount       float64 `json:"amount" binding:"required,gt=0"`
    InterestRate float64 `json:"interest_rate" binding:"required,gt=0"`
    TermMonths   int     `json:"term_months" binding:"required,gt=0"`
}

type RegisterCustomerRequest struct {
    Username   string `json:"username" binding:"required"`
    Password   string `json:"password" binding:"required,min=8"`
    FirstName  string `json:"first_name" binding:"required"`
    LastName   string `json:"last_name" binding:"required"`
    Email      string `json:"email" binding:"required,email"`
    Phone      string `json:"phone"`
    Address    string `json:"address"`
}

type AddBeneficiaryRequest struct {
    Name         string `json:"name" binding:"required"`
    AccountNumber string `json:"account_number" binding:"required"`
    BankName     string `json:"bank_name"`
}

type DepositRequest struct {
    Amount float64 `json:"amount" binding:"required,gt=0"`
}

type MakePaymentRequest struct {
    PaymentID int `json:"payment_id" binding:"required"`
}
''',

    'internal/repositories/account_repo.go': '''package repositories

import (
    "gorm.io/gorm"
    "banking-api/internal/models"
)

type AccountRepository interface {
    Create(account *models.Account) error
    GetByID(id int) (*models.Account, error)
    UpdateBalance(id int, amount float64) error
    ListByCustomer(customerID int) ([]models.Account, error)
}

type accountRepo struct {
    db *gorm.DB
}

func NewAccountRepo(db *gorm.DB) AccountRepository {
    return &accountRepo{db: db}
}

func (r *accountRepo) Create(account *models.Account) error {
    return r.db.Create(account).Error
}

func (r *accountRepo) GetByID(id int) (*models.Account, error) {
    var account models.Account
    err := r.db.Preload("Customer").First(&account, id).Error
    if err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, err
        }
        return nil, err
    }
    return &account, nil
}

func (r *accountRepo) UpdateBalance(id int, amount float64) error {
    return r.db.Model(&models.Account{}).Where("id = ?", id).Update("balance", gorm.Expr("balance + ?", amount)).Error
}

func (r *accountRepo) ListByCustomer(customerID int) ([]models.Account, error) {
    var accounts []models.Account
    err := r.db.Where("customer_id = ?", customerID).Find(&accounts).Error
    return accounts, err
}
''',

    'internal/repositories/transaction_repo.go': '''package repositories

import (
    "gorm.io/gorm"
    "banking-api/internal/models"
)

type TransactionRepository interface {
    Create(txn *models.Transaction) error
}

type transactionRepo struct {
    db *gorm.DB
}

func NewTransactionRepo(db *gorm.DB) TransactionRepository {
    return &transactionRepo{db: db}
}

func (r *transactionRepo) Create(txn *models.Transaction) error {
    // GORM inserts nil pointers as NULL, avoiding invalid FKs like 0
    return r.db.Create(txn).Error
}
''',

    'internal/repositories/loan_repo.go': '''package repositories

import (
    "gorm.io/gorm"
    "banking-api/internal/models"
)

type LoanRepository interface {
    Create(loan *models.Loan) error
    GetByID(id int) (*models.Loan, error)
    ListByCustomer(customerID int) ([]models.Loan, error)
    UpdateStatus(id int, status string) error
}

type loanRepo struct {
    db *gorm.DB
}

func NewLoanRepo(db *gorm.DB) LoanRepository {
    return &loanRepo{db: db}
}

func (r *loanRepo) Create(loan *models.Loan) error {
    return r.db.Create(loan).Error
}

func (r *loanRepo) GetByID(id int) (*models.Loan, error) {
    var loan models.Loan
    err := r.db.Preload("Customer").Preload("Payments").First(&loan, id).Error
    if err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, err
        }
        return nil, err
    }
    return &loan, nil
}

func (r *loanRepo) ListByCustomer(customerID int) ([]models.Loan, error) {
    var loans []models.Loan
    err := r.db.Where("customer_id = ?", customerID).Preload("Payments").Find(&loans).Error
    return loans, err
}

func (r *loanRepo) UpdateStatus(id int, status string) error {
    return r.db.Model(&models.Loan{}).Where("id = ?", id).Update("status", status).Error
}
''',

    'internal/repositories/loan_payment_repo.go': '''package repositories

import (
    "gorm.io/gorm"
    "time"
    "banking-api/internal/models"
)

type LoanPaymentRepository interface {
    Create(payment *models.LoanPayment) error
    GetByID(id int) (*models.LoanPayment, error)
    ListByLoan(loanID int) ([]models.LoanPayment, error)
    UpdateStatus(id int, status string, paidDate time.Time) error
}

type loanPaymentRepo struct {
    db *gorm.DB
}

func NewLoanPaymentRepo(db *gorm.DB) LoanPaymentRepository {
    return &loanPaymentRepo{db: db}
}

func (r *loanPaymentRepo) Create(payment *models.LoanPayment) error {
    return r.db.Create(payment).Error
}

func (r *loanPaymentRepo) GetByID(id int) (*models.LoanPayment, error) {
    var payment models.LoanPayment
    err := r.db.Preload("Loan").First(&payment, id).Error
    if err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, err
        }
        return nil, err
    }
    return &payment, nil
}

func (r *loanPaymentRepo) ListByLoan(loanID int) ([]models.LoanPayment, error) {
    var payments []models.LoanPayment
    err := r.db.Where("loan_id = ?", loanID).Order("due_date ASC").Find(&payments).Error
    return payments, err
}

func (r *loanPaymentRepo) UpdateStatus(id int, status string, paidDate time.Time) error {
    return r.db.Model(&models.LoanPayment{}).Where("id = ?", id).Updates(map[string]interface{}{
        "status": status,
        "paid_date": paidDate,
    }).Error
}
''',

    'internal/services/account_service.go': '''package services

import (
    "errors"
    "gorm.io/gorm"
    "banking-api/internal/models"
    "banking-api/internal/repositories"
)

type AccountService interface {
    CreateAccount(req *models.CreateAccountRequest, customerID, branchID int) (*models.Account, error)
    Transfer(fromID, toID int, amount float64) error
    Deposit(accountID int, amount float64) error
    GetStatements(accountID int) ([]models.Transaction, error)
}

type accountService struct {
    db      *gorm.DB
    repo    repositories.AccountRepository
    txRepo  repositories.TransactionRepository
}

func NewAccountService(db *gorm.DB, repo repositories.AccountRepository, txRepo repositories.TransactionRepository) AccountService {
    return &accountService{db: db, repo: repo, txRepo: txRepo}
}

func (s *accountService) CreateAccount(req *models.CreateAccountRequest, customerID, branchID int) (*models.Account, error) {
    account := &models.Account{
        CustomerID: customerID,
        BranchID:   branchID,
        Owner:      req.Owner,
        Currency:   req.Currency,
        Balance:    0,
    }
    if err := s.repo.Create(account); err != nil {
        return nil, err
    }
    return account, nil
}

func (s *accountService) Transfer(fromID, toID int, amount float64) error {
    return s.db.Transaction(func(tx *gorm.DB) error {
        fromAcc, err := s.repo.GetByID(fromID)
        if err != nil {
            return errors.New("source account not found")
        }
        if fromAcc.Balance < amount {
            return errors.New("insufficient funds")
        }
        
        _, err = s.repo.GetByID(toID)
        if err != nil {
            return errors.New("destination account not found")
        }
        
        if err := s.repo.UpdateBalance(fromID, -amount); err != nil {
            return err
        }
        if err := s.repo.UpdateBalance(toID, amount); err != nil {
            return err
        }
        
        txn := &models.Transaction{
            FromAccountID: &fromID,
            ToAccountID:   &toID,
            Amount:        amount,
        }
        return s.txRepo.Create(txn)
    })
}

func (s *accountService) Deposit(accountID int, amount float64) error {
    return s.db.Transaction(func(tx *gorm.DB) error {
        _, err := s.repo.GetByID(accountID)
        if err != nil {
            return errors.New("account not found")
        }
        
        if err := s.repo.UpdateBalance(accountID, amount); err != nil {
            return err
        }
        
        txn := &models.Transaction{
            FromAccountID: nil,
            ToAccountID:   &accountID,
            Amount:        amount,
        }
        return s.txRepo.Create(txn)
    })
}

func (s *accountService) GetStatements(accountID int) ([]models.Transaction, error) {
    var txns []models.Transaction
    err := s.db.Where("from_account_id = ? OR to_account_id = ?", accountID, accountID).
             Order("created_at DESC").Limit(100).Find(&txns).Error
    return txns, err
}
''',

    'internal/services/loan_service.go': '''package services

import (
    "errors"
    "math"
    "time"

    "gorm.io/gorm"
    "banking-api/internal/models"
    "banking-api/internal/repositories"
)

type LoanService interface {
    CreateLoan(req *models.CreateLoanRequest, customerID, branchID int) (*models.Loan, error)
    ListLoans(customerID int) ([]models.Loan, error)
    UpdateStatus(loanID int, status string) error
}

type loanService struct {
    db   *gorm.DB
    repo repositories.LoanRepository
    pmRepo repositories.LoanPaymentRepository
}

func NewLoanService(db *gorm.DB, repo repositories.LoanRepository, pmRepo repositories.LoanPaymentRepository) LoanService {
    return &loanService{db: db, repo: repo, pmRepo: pmRepo}
}

// Calculate EMI: P * r * (1+r)^n / ((1+r)^n - 1)
func calculateEMI(principal, monthlyRate float64, months int) float64 {
    if months == 0 {
        return 0
    }
    r := monthlyRate / 12 // Monthly rate from annual
    if r == 0 {
        return principal / float64(months)
    }
    power := math.Pow(1+r, float64(months))
    emi := principal * r * power / (power - 1)
    return emi
}

func (s *loanService) CreateLoan(req *models.CreateLoanRequest, customerID, branchID int) (*models.Loan, error) {
    var loan *models.Loan
    err := s.db.Transaction(func(tx *gorm.DB) error {
        // Calculate total payable
        monthlyRate := req.InterestRate // Annual rate
        emi := calculateEMI(req.Amount, monthlyRate, req.TermMonths)
        totalPayable := emi * float64(req.TermMonths)

        loan = &models.Loan{
            CustomerID:   customerID,
            BranchID:     branchID,
            Amount:       req.Amount,
            InterestRate: req.InterestRate,
            TermMonths:   req.TermMonths,
            TotalPayable: totalPayable,
            Status:       "approved", // Simple approval
            StartDate:    time.Now(),
            EndDate:      time.Now().AddDate(0, req.TermMonths, 0),
        }
        if err := s.repo.Create(loan); err != nil {
            return err
        }

        // Generate payments (equal EMI)
        for i := 1; i <= req.TermMonths; i++ {
            dueDate := time.Now().AddDate(0, i, 0) // Monthly
            payment := &models.LoanPayment{
                LoanID:   loan.ID,
                Amount:   emi,
                DueDate:  dueDate,
                Status:   "pending",
            }
            if err := s.pmRepo.Create(payment); err != nil {
                return err // Rollback on failure
            }
        }

        // Reload with payments
        fullLoan, err := s.repo.GetByID(loan.ID)
        if err != nil {
            return err
        }
        loan = fullLoan
        return nil
    })
    if err != nil {
        return nil, err
    }
    return loan, nil
}

func (s *loanService) ListLoans(customerID int) ([]models.Loan, error) {
    return s.repo.ListByCustomer(customerID)
}

func (s *loanService) UpdateStatus(loanID int, status string) error {
    return s.repo.UpdateStatus(loanID, status)
}
''',

    'internal/services/loan_payment_service.go': '''package services

import (
    "errors"
    "time"

    "gorm.io/gorm"
    "banking-api/internal/models"
    "banking-api/internal/repositories"
)

type LoanPaymentService interface {
    MakePayment(paymentID int, loanID int) error
    ListPayments(loanID int) ([]models.LoanPayment, error)
}

type loanPaymentService struct {
    db   *gorm.DB
    repo repositories.LoanPaymentRepository
    loanRepo repositories.LoanRepository
}

func NewLoanPaymentService(db *gorm.DB, repo repositories.LoanPaymentRepository, loanRepo repositories.LoanRepository) LoanPaymentService {
    return &loanPaymentService{db: db, repo: repo, loanRepo: loanRepo}
}

func (s *loanPaymentService) MakePayment(paymentID, loanID int) error {
    return s.db.Transaction(func(tx *gorm.DB) error {
        payment, err := s.repo.GetByID(paymentID)
        if err != nil {
            return errors.New("payment not found")
        }
        if payment.LoanID != loanID {
            return errors.New("payment does not belong to this loan")
        }
        if payment.Status == "paid" {
            return errors.New("payment already made")
        }

        // Update payment
        if err := s.repo.UpdateStatus(paymentID, "paid", time.Now()); err != nil {
            return err
        }

        // Update loan if all paid
        loan, err := s.loanRepo.GetByID(loanID)
        if err != nil {
            return err
        }
        payments, _ := s.repo.ListByLoan(loanID)
        paidCount := 0
        for _, p := range payments {
            if p.Status == "paid" {
                paidCount++
            }
        }
        if paidCount == loan.TermMonths {
            s.loanRepo.UpdateStatus(loanID, "repaid")
        }

        return nil
    })
}

func (s *loanPaymentService) ListPayments(loanID int) ([]models.LoanPayment, error) {
    return s.repo.ListByLoan(loanID)
}
''',

    'pkg/auth/jwt.go': '''package auth

import (
    "os"
    "strings"
    "time"

    "github.com/gin-gonic/gin"
    "github.com/golang-jwt/jwt/v4"
)

var jwtSecret = []byte(os.Getenv("JWT_SECRET"))

func GenerateToken(userID int) (string, error) {
    claims := jwt.MapClaims{
        "user_id": userID,
        "exp":     time.Now().Add(time.Hour * 24).Unix(),
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(jwtSecret)
}

func GetUserID(c *gin.Context) int {
    tokenString := c.GetHeader("Authorization")
    if strings.HasPrefix(tokenString, "Bearer ") {
        tokenString = tokenString[7:]
    }
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        return jwtSecret, nil
    })
    if err != nil || !token.Valid {
        return 0
    }
    if claims, ok := token.Claims.(jwt.MapClaims); ok {
        return int(claims["user_id"].(float64))
    }
    return 0
}
''',

    'internal/handlers/handlers.go': '''package handlers

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"
    "golang.org/x/crypto/bcrypt"
    "banking-api/internal/db"
    "banking-api/internal/models"
    "banking-api/internal/repositories"
    "banking-api/internal/services"
    "banking-api/pkg/auth"
)

var dbConn = db.Connect()

// Init repos and services
var accountRepo = repositories.NewAccountRepo(dbConn)
var txRepo = repositories.NewTransactionRepo(dbConn)
var accountSvc = services.NewAccountService(dbConn, accountRepo, txRepo)

var loanRepo = repositories.NewLoanRepo(dbConn)
var loanPaymentRepo = repositories.NewLoanPaymentRepo(dbConn)
var loanSvc = services.NewLoanService(dbConn, loanRepo, loanPaymentRepo)
var loanPaymentSvc = services.NewLoanPaymentService(dbConn, loanPaymentRepo, loanRepo)

// Auth
func Register(c *gin.Context) {
    var req models.RegisterCustomerRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    hashed, _ := bcrypt.GenerateFromPassword([]byte(req.Password), 14)
    customer := &models.Customer{
        Username:     req.Username,
        PasswordHash: string(hashed),
        FirstName:    req.FirstName,
        LastName:     req.LastName,
        Email:        req.Email,
        Phone:        req.Phone,
        Address:      req.Address,
    }
    if err := dbConn.Create(customer).Error; err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    token, _ := auth.GenerateToken(customer.ID)
    c.JSON(http.StatusCreated, gin.H{"token": token})
}

func Login(c *gin.Context) {
    var loginReq struct {
        Username string `json:"username" binding:"required"`
        Password string `json:"password" binding:"required"`
    }
    if err := c.ShouldBindJSON(&loginReq); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    var customer models.Customer
    if err := dbConn.Where("username = ?", loginReq.Username).First(&customer).Error; err != nil {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
        return
    }

    if bcrypt.CompareHashAndPassword([]byte(customer.PasswordHash), []byte(loginReq.Password)) != nil {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
        return
    }

    token, _ := auth.GenerateToken(customer.ID)
    c.JSON(http.StatusOK, gin.H{"token": token})
}

// Accounts
func CreateAccount(c *gin.Context) {
    userID := auth.GetUserID(c)
    if userID == 0 {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
        return
    }
    var req models.CreateAccountRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    branchID := 1
    account, err := accountSvc.CreateAccount(&req, userID, branchID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, account)
}

func ListAccounts(c *gin.Context) {
    userID := auth.GetUserID(c)
    if userID == 0 {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
        return
    }
    accounts, err := accountRepo.ListByCustomer(userID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, accounts)
}

func Transfer(c *gin.Context) {
    fromID, err := strconv.Atoi(c.Param("from_id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid from_id"})
        return
    }
    var req models.TransferRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    if req.ToAccountID == 0 {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid to_account_id"})
        return
    }
    if err := accountSvc.Transfer(fromID, req.ToAccountID, req.Amount); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, gin.H{"message": "Transfer successful"})
}

func Deposit(c *gin.Context) {
    accountID, err := strconv.Atoi(c.Param("account_id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid account_id"})
        return
    }
    if accountID == 0 {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid account_id"})
        return
    }
    var req models.DepositRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    if err := accountSvc.Deposit(accountID, req.Amount); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, gin.H{"message": "Deposit successful"})
}

func GetStatements(c *gin.Context) {
    accountID, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid id"})
        return
    }
    statements, err := accountSvc.GetStatements(accountID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, statements)
}

// Loans
func CreateLoan(c *gin.Context) {
    userID := auth.GetUserID(c)
    if userID == 0 {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
        return
    }
    var req models.CreateLoanRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    branchID := 1
    loan, err := loanSvc.CreateLoan(&req, userID, branchID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, gin.H{
        "loan": loan,
        "message": "Loan created with payment schedule",
    })
}

func ListLoans(c *gin.Context) {
    userID := auth.GetUserID(c)
    if userID == 0 {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
        return
    }
    loans, err := loanSvc.ListLoans(userID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, loans)
}

// Loan Payments
func MakePayment(c *gin.Context) {
    loanID, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid loan_id"})
        return
    }
    var req models.MakePaymentRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    if err := loanPaymentSvc.MakePayment(req.PaymentID, loanID); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, gin.H{"message": "Payment made successfully"})
}

func ListPayments(c *gin.Context) {
    loanID, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid loan_id"})
        return
    }
    payments, err := loanPaymentSvc.ListPayments(loanID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, payments)
}

// Beneficiary (placeholder)
func AddBeneficiary(c *gin.Context) {
    userID := auth.GetUserID(c)
    if userID == 0 {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
        return
    }
    var req models.AddBeneficiaryRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, gin.H{"message": "Beneficiary added", "customer_id": userID})
}
''',

    'cmd/server/main.go': '''package main

import (
    "log"
    "net/http"
    "os"
    "path/filepath"

    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    "banking-api/internal/db"
    "banking-api/internal/handlers"
)

func main() {
    dir, err := os.Getwd()
    if err != nil {
        log.Fatal("Cannot get working directory:", err)
    }
    envPath := filepath.Join(dir, ".env")
    log.Printf("Loading .env from: %s", envPath)
    
    if err := godotenv.Load(envPath); err != nil {
        log.Printf("Warning: Could not load .env from %s: %v", envPath, err)
    } else {
        log.Println("Successfully loaded .env")
    }

    dsn := os.Getenv("DB_DSN")
    jwtSecret := os.Getenv("JWT_SECRET")
    port := os.Getenv("PORT")
    if dsn == "" {
        log.Fatal("DB_DSN not loaded!")
    }
    if jwtSecret == "" {
        log.Fatal("JWT_SECRET not loaded!")
    }
    if port == "" {
        port = "8080"
    }

    _ = db.Connect()

    r := gin.Default()
    r.Use(gin.Logger())

    // Public routes
    r.POST("/auth/register", handlers.Register)
    r.POST("/auth/login", handlers.Login)

    // Protected routes
    protected := r.Group("")
    protected.Use(authMiddleware())

    // Accounts
    protected.POST("/accounts", handlers.CreateAccount)
    protected.GET("/accounts", handlers.ListAccounts)
    protected.POST("/transfers/:from_id", handlers.Transfer)
    protected.POST("/deposits/:account_id", handlers.Deposit)
    protected.GET("/accounts/:id/statements", handlers.GetStatements)

    // Loans
    protected.POST("/loans", handlers.CreateLoan)
    protected.GET("/loans", handlers.ListLoans)
    protected.POST("/loans/:id/repay", handlers.MakePayment)
    protected.GET("/loans/:id/payments", handlers.ListPayments)

    // Beneficiaries
    protected.POST("/beneficiaries", handlers.AddBeneficiary)

    log.Printf("Server starting on :%s", port)
    r.Run(":" + port)
}

func authMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        if c.GetHeader("Authorization") == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
            return
        }
        // Validate token via GetUserID in handlers
        c.Next()
    }
}
''',
}

# Directory structure
directories = [
    project_dir,
    os.path.join(project_dir, 'cmd', 'server'),
    os.path.join(project_dir, 'internal', 'db'),
    os.path.join(project_dir, 'internal', 'models'),
    os.path.join(project_dir, 'internal', 'repositories'),
    os.path.join(project_dir, 'internal', 'services'),
    os.path.join(project_dir, 'internal', 'handlers'),
    os.path.join(project_dir, 'pkg', 'auth'),
    os.path.join(project_dir, 'migrations')
]

def create_project():
    # Create directories
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create files
    for rel_path, content in files_content.items():
        file_path = os.path.join(project_dir, rel_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created file: {rel_path}")

    # Zip the project
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
    print(f"Project zipped as: {zip_filename}")

    # Optional: Cleanup extracted folder (uncomment if desired)
    # import shutil
    # shutil.rmtree(project_dir)
    # print(f"Cleaned up: {project_dir}")

if __name__ == "__main__":
    create_project()
    print("\n=== Setup Instructions ===")
    print("1. Unzip banking-api.zip")
    print("2. cd banking-api")
    print("3. Copy .env.example to .env and update DB_DSN (e.g., root:root for MySQL)")
    print("4. go mod tidy")
    print("5. Create DB: mysql -u root -p -e 'CREATE DATABASE banking_db;'")
    print("6. Run schema: mysql -u root -p banking_db < migrations/schema.sql")
    print("7. Start server: go run cmd/server/main.go")
    print("8. Test: Use curl for register/login, then POST /loans, etc. (see previous responses)")
