package mysql

import (
    "database/sql"

    "cinema-booking/internal/domain"
    "golang.org/x/crypto/bcrypt"
)

type UserRepository struct {
    db *sql.DB
}

func NewUserRepository(db *sql.DB) *UserRepository {
    return &UserRepository{db: db}
}

func (r *UserRepository) Create(user *domain.User) error {
    hashed, err := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.DefaultCost)
    if err != nil {
        return err
    }
    query := `INSERT INTO users (username, email, password) VALUES (?, ?, ?)`
    res, err := r.db.Exec(query, user.Username, user.Email, string(hashed))
    if err != nil {
        return err
    }
    id, _ := res.LastInsertId()
    user.ID = int(id)
    return nil
}

func (r *UserRepository) GetByEmail(email string) (*domain.User, error) {
    query := `SELECT id, username, email, password FROM users WHERE email = ?`
    row := r.db.QueryRow(query, email)
    var u domain.User
    err := row.Scan(&u.ID, &u.Username, &u.Email, &u.Password)
    if err != nil {
        return nil, err
    }
    return &u, nil
}

func (r *UserRepository) GetByID(id int) (*domain.User, error) {
    query := `SELECT id, username, email FROM users WHERE id = ?`
    row := r.db.QueryRow(query, id)
    var u domain.User
    err := row.Scan(&u.ID, &u.Username, &u.Email)
    if err != nil {
        return nil, err
    }
    return &u, nil
}
