package repositories

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
