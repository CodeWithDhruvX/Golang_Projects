### Testing the Banking API with Sample Payloads

To test the banking API, ensure the server is running (`go run cmd/server/main.go` from the project root, confirming "Server starting on :8080" with no errors) and MySQL is connected (tables exist via AutoMigrate). Use curl in PowerShell (or Postman/Insomnia for GUI) to hit endpoints on http://localhost:8080. Tests cover authentication, account management, transfers, deposits, statements, loans, and beneficiaries, using sample JSON payloads from the models. Each step includes the command, expected response (HTTP status and body), and verification notes.[1][2]

### Prerequisites

- **Server Running**: Navigate to `C:\Users\dhruv\Downloads\Interview_questions\Golang\golang_projects\banking-api` and run `go run cmd/server/main.go`. It should log successful DB connection.
- **Curl**: PowerShell has curl built-in; if issues, use Git Bash or install via `winget install curl`.
- **JWT Token**: Protected routes require `Authorization: Bearer <token>` header from login/register response.
- **MySQL Verification**: Check data post-tests: `mysql -u root -p -e "USE banking_db; SELECT * FROM customers;"` (enter 'root' password).[3]
- **Cleanup**: For retries, drop/recreate DB or truncate tables via MySQL shell.

Start tests in a new PowerShell window in the project root.

### Step 1: Register a New Customer (POST /auth/register)

This creates a user and returns a JWT token for subsequent requests.

**Command** (copy-paste into PowerShell):
```
curl -X POST http://localhost:8080/auth/register -H "Content-Type: application/json" -d '{
  "username": "johndoe",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, Mumbai"
}'
```

**Expected Response**:
- Status: 201 Created
- Body: `{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}` (JWT token)
- Example: `{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MzA5ODI5NjB9.abc123"}`

**Verification**: Copy the `token` value (e.g., "eyJ..."). Check MySQL: `mysql -u root -p -e "USE banking_db; SELECT id, username, email FROM customers;"`—should show the new user (ID=1). If 400 Bad Request, check payload validation (e.g., password min=8).[4]

### Step 2: Login with Credentials (POST /auth/login)

Authenticates and returns a fresh JWT token (expires in 24h).

**Command** (use registered creds):
```
curl -X POST http://localhost:8080/auth/login -H "Content-Type: application/json" -d '{
  "username": "johndoe",
  "password": "securepass123"
}'
```

**Expected Response**:
- Status: 200 OK
- Body: `{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}` (new token)
- Example: Similar to register, but for ID=1.

**Verification**: Use this new token for protected calls. If 401 Unauthorized, creds mismatch—retry register. Test invalid login: Change password to "wrong"—gets `{"error":"Invalid credentials"}`.[2]

### Step 3: Create an Account (POST /accounts)

Protected: Creates an account for the authenticated customer (uses userID from token).

**Command** (replace `<TOKEN>` with your token from Step 2):
```
curl -X POST http://localhost:8080/accounts -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{
  "owner": "John Doe Savings",
  "currency": "USD"
}'
```

**Expected Response**:
- Status: 201 Created
- Body: `{"id":1,"customer_id":1,"branch_id":1,"owner":"John Doe Savings","balance":0,"currency":"USD","created_at":"2025-10-22T11:50:00Z"}` (account details)
- Note: branch_id=1 (default; sample branch from schema).

**Verification**: MySQL: `mysql -u root -p -e "USE banking_db; SELECT * FROM accounts;"`—shows new account linked to customer_id=1. If 401, token invalid—re-login. Create another: Repeat with `"owner": "John Doe Checking"`—gets ID=2.[1]

### Step 4: List Accounts (GET /accounts)

Protected: Retrieves all accounts for the authenticated customer.

**Command**:
```
curl -X GET http://localhost:8080/accounts -H "Authorization: Bearer <TOKEN>"
```

**Expected Response**:
- Status: 200 OK
- Body: Array of accounts, e.g., `[{"id":1,"customer_id":1,"branch_id":1,"owner":"John Doe Savings","balance":0,"currency":"USD","created_at":"2025-10-22T11:50:00Z"}, {"id":2,...}]`

**Verification**: Lists only the user's accounts. If empty after Step 3, check token/userID mapping.[5]

### Step 5: Make a Deposit (POST /deposits/:account_id)

Protected: Adds funds to an account atomically (updates balance and logs transaction).

**Command** (use account_id=1 from Step 3):
```
curl -X POST http://localhost:8080/deposits/1 -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{
  "amount": 1000.50
}'
```

**Expected Response**:
- Status: 200 OK
- Body: `{"message":"Deposit successful"}`

**Verification**: MySQL: `mysql -u root -p -e "USE banking_db; SELECT balance FROM accounts WHERE id=1;"`—balance=1000.50. Check transactions: `SELECT * FROM transactions WHERE to_account_id=1;`—new deposit log (amount=1000.50, from_account_id=NULL). If insufficient validation error, ensure account exists.[6]

### Step 6: Perform a Transfer (POST /transfers/:from_id)

Protected: Transfers funds between accounts (assumes two accounts; create second in Step 3). Atomic: Checks balance, updates both, logs transaction.

**Command** (from_id=1, to_id=2, amount < balance):
```
curl -X POST http://localhost:8080/transfers/1 -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{
  "to_account_id": 2,
  "amount": 500.00
}'
```

**Expected Response**:
- Status: 200 OK
- Body: `{"message":"Transfer successful"}`

**Verification**: MySQL:
- Accounts: Balance ID=1: 500.50; ID=2: 500.00.
- Transactions: `SELECT * FROM transactions WHERE from_account_id=1 AND to_account_id=2;`—log with amount=500.00.
- If "insufficient funds" (400 Bad Request), deposit more first. Test negative amount: Gets binding error.[5][6]

### Step 7: Get Account Statements (GET /accounts/:id/statements)

Protected: Retrieves recent transactions (last 100) for an account.

**Command** (for account_id=1):
```
curl -X GET http://localhost:8080/accounts/1/statements -H "Authorization: Bearer <TOKEN>"
```

**Expected Response**:
- Status: 200 OK
- Body: Array of transactions, e.g., `[{"id":2,"from_account_id":1,"to_account_id":2,"amount":500,"created_at":"2025-10-22T11:55:00Z"}, {"id":1,"to_account_id":1,"amount":1000.5,"created_at":"2025-10-22T11:50:00Z"}]`

**Verification**: Matches deposits/transfers from Steps 5-6. Ordered DESC by created_at; includes deposits (from_account_id=NULL).[1]

### Step 8: Create a Loan (POST /loans) - Placeholder Test

Protected: Submits a loan application (uses userID internally).

**Command**:
```
curl -X POST http://localhost:8080/loans -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{
  "amount": 50000.00,
  "interest_rate": 0.05,
  "term_months": 12
}'
```

**Expected Response**:
- Status: 201 Created
- Body: `{"loan_id":1,"status":"pending","customer_id":1}` (from placeholder; expand service for full logic)

**Verification**: MySQL: `SELECT * FROM loans WHERE customer_id=1;`—new loan record. For full impl, add loan service to persist.[7]

### Step 9: Add a Beneficiary (POST /beneficiaries) - Placeholder Test

Protected: Adds a transfer beneficiary for the customer.

**Command**:
```
curl -X POST http://localhost:8080/beneficiaries -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{
  "name": "Jane Smith",
  "account_number": "123456789012",
  "bank_name": "ABC Bank"
}'
```

**Expected Response**:
- Status: 201 Created
- Body: `{"message":"Beneficiary added","customer_id":1}`

**Verification**: MySQL: `SELECT * FROM beneficiaries WHERE customer_id=1;`—new record. Integrate with transfers for beneficiary-based sends in future.[7]

### Post-Testing Verification and Troubleshooting

- **Full Flow Summary**: Register → Login (get token) → Create 2 accounts → Deposit to first → Transfer between → Check statements → Optional: Loans/Beneficiaries.
- **Error Handling**:
  - 401 Unauthorized: Invalid/missing token—re-login.
  - 400 Bad Request: Payload issues (e.g., missing fields, amount<=0)—validate JSON.
  - 500 Internal Server Error: DB issues—check MySQL logs (`SHOW ENGINE INNODB STATUS;`); ensure foreign keys intact.
  - No data: Token userID mismatch—verify customer_id in responses.
- **Advanced Testing**: Use Postman collection (import endpoints with auth pre-request script for token). For load, tools like Apache Bench (`ab -n 100 -c 10 http://localhost:8080/accounts -H "Authorization: Bearer <TOKEN>"`). Add unit tests with `go test` using testify mocks.[2][4]
- **Cleanup**: Truncate: `mysql -u root -p -e "USE banking_db; TRUNCATE TABLE customers, accounts, transactions, loans, loan_payments, beneficiaries;"` (branches static).

This sequence validates core CRUD, auth, and transactions atomically. If a step fails, share the exact response for debugging!

[1](https://www.honeybadger.io/blog/how-to-create-crud-application-with-golang-and-mysql/)
[2](https://www.red-gate.com/simple-talk/development/other-development/building-rest-apis-in-go-with-mux-and-gorm/)
[3](https://www.getgalaxy.io/learn/common-errors/mysql-error-1824-er-fk-cannot-open-parent-failed-to-open-referenced-table---how-to-fix-and-prevent)
[4](https://www.youtube.com/watch?v=7VLmLOiQ3ck)
[5](https://github.com/techschool/simplebank)
[6](https://www.geeksforgeeks.org/sql/how-to-design-a-database-for-online-banking-system/)
[7](https://vertabelo.com/blog/database-design-for-banking-system/)




https://www.perplexity.ai/search/backing-system-rest-api-full-p-GAO6vW5eTtSGqVfHKDaz3A