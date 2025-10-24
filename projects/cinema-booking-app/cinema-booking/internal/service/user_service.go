package service

import (
    "time"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/repository/mysql"
    "golang.org/x/crypto/bcrypt"

    "github.com/golang-jwt/jwt/v5"
)

type UserService struct {
    repo *mysql.UserRepository
    jwtSecret string
}

func NewUserService(repo *mysql.UserRepository, secret string) *UserService {
    return &UserService{repo: repo, jwtSecret: secret}
}

func (s *UserService) Register(req *domain.RegisterRequest) (*domain.User, error) {
    if req.Email == "" || req.Password == "" {
        return nil, domain.ErrInvalidCredentials
    }
    user := &domain.User{Username: req.Username, Email: req.Email, Password: req.Password}
    if err := s.repo.Create(user); err != nil {
        return nil, err
    }
    return user, nil
}

func (s *UserService) Login(req *domain.LoginRequest) (string, error) {
    user, err := s.repo.GetByEmail(req.Email)
    if err != nil {
        return "", domain.ErrUserNotFound
    }
    if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
        return "", domain.ErrInvalidCredentials
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "user_id": user.ID,
        "exp":     time.Now().Add(time.Hour * 24).Unix(),
    })
    tokenString, err := token.SignedString([]byte(s.jwtSecret))
    if err != nil {
        return "", err
    }
    return tokenString, nil
}

func (s *UserService) GetUser(id int) (*domain.User, error) {
    return s.repo.GetByID(id)
}
