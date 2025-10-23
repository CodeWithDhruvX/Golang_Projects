-- Banking API Database Schema (supports all features: loans with total_payable)
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
