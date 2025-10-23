package handlers

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
