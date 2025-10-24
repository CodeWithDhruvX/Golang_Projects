import os
import zipfile
from pathlib import Path

# Define the project structure and file contents
project_structure = {
    'cinema-booking': {
        'cmd/app/main.go': '''package main

import (
    "database/sql"
    "fmt"
    "log"
    "time"

    _ "github.com/go-sql-driver/mysql"

    "cinema-booking/config"
    "cinema-booking/internal/handler/http"
    "cinema-booking/internal/middleware"
    "cinema-booking/internal/repository/mysql"
    "cinema-booking/internal/service"
)

func main() {
    cfg := config.LoadConfig()

    // DB connection
    dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true",
        cfg.DBUser, cfg.DBPassword, cfg.DBHost, cfg.DBPort, cfg.DBName)
    db, err := sql.Open("mysql", dsn)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Init schema
    initSchema(db)

    app := &http.App{}
    app.Initialize(db, cfg)
    app.Run(cfg.ServerPort)
}

func initSchema(db *sql.DB) {
    queries := []string{
        `CREATE DATABASE IF NOT EXISTS cinema_db`,
        `USE cinema_db`,
        `CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            duration_minutes INT NOT NULL,
            genre VARCHAR(100)
        )`,
        `CREATE TABLE IF NOT EXISTS shows (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT,
            theater_id INT,
            show_time DATETIME NOT NULL,
            total_seats INT NOT NULL,
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (theater_id) REFERENCES theaters(id)
        )`,
        `CREATE TABLE IF NOT EXISTS seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            show_id INT,
            seat_number VARCHAR(50) NOT NULL,
            is_booked BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (show_id) REFERENCES shows(id)
        )`,
        `CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            show_id INT,
            seat_ids JSON,
            user_id INT,
            user_name VARCHAR(255) NOT NULL,
            booked_at DATETIME NOT NULL,
            FOREIGN KEY (show_id) REFERENCES shows(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )`,
        `CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )`,
        `CREATE TABLE IF NOT EXISTS theaters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            capacity INT NOT NULL
        )`,
    }
    for _, q := range queries {
        if _, err := db.Exec(q); err != nil {
            log.Printf("Schema init error: %v", err)
        }
    }
}
''',
        'config/config.go': '''package config

import (
    "os"
    "strconv"
    "log"

    "github.com/joho/godotenv"
)

type Config struct {
    DBHost     string
    DBPort     string
    DBUser     string
    DBPassword string
    DBName     string
    ServerPort string
    JWT_SECRET string
}

func LoadConfig() *Config {
    if err := godotenv.Load(); err != nil {
        log.Println("No .env file found")
    }

    return &Config{
        DBHost:     os.Getenv("DB_HOST"),
        DBPort:     os.Getenv("DB_PORT"),
        DBUser:     os.Getenv("DB_USER"),
        DBPassword: os.Getenv("DB_PASSWORD"),
        DBName:     os.Getenv("DB_NAME"),
        ServerPort: os.Getenv("SERVER_PORT"),
        JWT_SECRET: os.Getenv("JWT_SECRET"),
    }
}
''',
        '.env': '''DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=cinema_db
SERVER_PORT=8080
JWT_SECRET=your-super-secret-jwt-key-change-this-in-prod
''',
        'go.mod': '''module cinema-booking

go 1.21

require (
    github.com/gorilla/mux v1.8.1
    github.com/joho/godotenv v1.5.1
    github.com/go-sql-driver/mysql v1.7.1
    github.com/golang-jwt/jwt/v5 v5.0.0
    golang.org/x/crypto v0.17.0
)

require (
    github.com/andybalholm/brotli v1.0.5 // indirect
    github.com/gorilla/handlers v1.5.1 // indirect
    github.com/klauspost/compress v1.17.0 // indirect
    golang.org/x/net v0.19.0 // indirect
)
''',
        'internal/domain/entities.go': '''package domain

import "time"

type Movie struct {
    ID          int       `json:"id"`
    Title       string    `json:"title"`
    Duration    int       `json:"duration_minutes"`
    Genre       string    `json:"genre"`
}

type Show struct {
    ID          int       `json:"id"`
    MovieID     int       `json:"movie_id"`
    TheaterID   int       `json:"theater_id"`
    ShowTime    time.Time `json:"show_time"`
    TotalSeats  int       `json:"total_seats"`
}

type Seat struct {
    ID        int `json:"id"`
    ShowID    int `json:"show_id"`
    SeatNumber string `json:"seat_number"`
    IsBooked  bool    `json:"is_booked"`
}

type Booking struct {
    ID      int       `json:"id"`
    ShowID  int       `json:"show_id"`
    SeatIDs []int     `json:"seat_ids"`
    UserID  int       `json:"user_id"`
    UserName string   `json:"user_name"`
    BookedAt time.Time `json:"booked_at"`
}

type User struct {
    ID       int    `json:"id"`
    Username string `json:"username"`
    Email    string `json:"email"`
    Password string `json:"-"`  // Not exposed
}

type Theater struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
    Location string `json:"location"`
    Capacity int `json:"capacity"`
}

type LoginRequest struct {
    Email    string `json:"email"`
    Password string `json:"password"`
}

type RegisterRequest struct {
    Username string `json:"username"`
    Email    string `json:"email"`
    Password string `json:"password"`
}

type CreateBookingRequest struct {
    ShowID  int      `json:"show_id"`
    SeatIDs []int    `json:"seat_ids"`
    UserID  int      `json:"user_id"`
}

type CancelBookingRequest struct {
    BookingID int `json:"booking_id"`
}
''',
        'internal/domain/errors.go': '''package domain

import "errors"

var (
    ErrMovieNotFound = errors.New("movie not found")
    ErrShowNotFound  = errors.New("show not found")
    ErrSeatNotAvailable = errors.New("seat not available")
    ErrBookingFailed    = errors.New("booking failed")
    ErrUserNotFound     = errors.New("user not found")
    ErrInvalidCredentials = errors.New("invalid email or password")
    ErrTokenInvalid     = errors.New("invalid token")
    ErrUnauthorized     = errors.New("unauthorized access")
    ErrBookingNotFound  = errors.New("booking not found")
    ErrNotOwner         = errors.New("not the booking owner")
    ErrTheaterNotFound  = errors.New("theater not found")
)
''',
        'internal/repository/mysql/movie_repository.go': '''package mysql

import (
    "database/sql"
    "fmt"

    "cinema-booking/internal/domain"
)

type MovieRepository struct {
    db *sql.DB
}

func NewMovieRepository(db *sql.DB) *MovieRepository {
    return &MovieRepository{db: db}
}

func (r *MovieRepository) Create(movie *domain.Movie) error {
    query := `INSERT INTO movies (title, duration_minutes, genre) VALUES (?, ?, ?)`
    res, err := r.db.Exec(query, movie.Title, movie.Duration, movie.Genre)
    if err != nil {
        return err
    }
    id, _ := res.LastInsertId()
    movie.ID = int(id)
    return nil
}

func (r *MovieRepository) GetByID(id int) (*domain.Movie, error) {
    query := `SELECT id, title, duration_minutes, genre FROM movies WHERE id = ?`
    row := r.db.QueryRow(query, id)
    var m domain.Movie
    err := row.Scan(&m.ID, &m.Title, &m.Duration, &m.Genre)
    if err != nil {
        return nil, err
    }
    return &m, nil
}

func (r *MovieRepository) List() ([]*domain.Movie, error) {
    query := `SELECT id, title, duration_minutes, genre FROM movies`
    rows, err := r.db.Query(query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var movies []*domain.Movie
    for rows.Next() {
        var m domain.Movie
        if err := rows.Scan(&m.ID, &m.Title, &m.Duration, &m.Genre); err != nil {
            return nil, err
        }
        movies = append(movies, &m)
    }
    return movies, nil
}
''',
        'internal/repository/mysql/show_repository.go': '''package mysql

import (
    "database/sql"
    "fmt"
    "time"

    "cinema-booking/internal/domain"
)

type ShowRepository struct {
    db *sql.DB
}

func NewShowRepository(db *sql.DB) *ShowRepository {
    return &ShowRepository{db: db}
}

func (r *ShowRepository) Create(show *domain.Show) error {
    query := `INSERT INTO shows (movie_id, theater_id, show_time, total_seats) VALUES (?, ?, ?, ?)`
    res, err := r.db.Exec(query, show.MovieID, show.TheaterID, show.ShowTime, show.TotalSeats)
    if err != nil {
        return err
    }
    id, _ := res.LastInsertId()
    show.ID = int(id)
    // Create seats
    seatRepo := NewSeatRepository(r.db)
    for i := 1; i <= show.TotalSeats; i++ {
        seat := &domain.Seat{ShowID: show.ID, SeatNumber: fmt.Sprintf("Seat_%d", i), IsBooked: false}
        if err := seatRepo.Create(seat); err != nil {
            return err
        }
    }
    return nil
}

func (r *ShowRepository) GetByID(id int) (*domain.Show, error) {
    query := `SELECT id, movie_id, theater_id, show_time, total_seats FROM shows WHERE id = ?`
    row := r.db.QueryRow(query, id)
    var s domain.Show
    err := row.Scan(&s.ID, &s.MovieID, &s.TheaterID, &s.ShowTime, &s.TotalSeats)
    if err != nil {
        return nil, err
    }
    return &s, nil
}

func (r *ShowRepository) List() ([]*domain.Show, error) {
    query := `SELECT id, movie_id, theater_id, show_time, total_seats FROM shows`
    rows, err := r.db.Query(query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var shows []*domain.Show
    for rows.Next() {
        var s domain.Show
        if err := rows.Scan(&s.ID, &s.MovieID, &s.TheaterID, &s.ShowTime, &s.TotalSeats); err != nil {
            return nil, err
        }
        shows = append(shows, &s)
    }
    return shows, nil
}

func (r *ShowRepository) Search(movieID *int, startTime *time.Time, endTime *time.Time) ([]*domain.Show, error) {
    query := `SELECT id, movie_id, theater_id, show_time, total_seats FROM shows WHERE 1=1`
    args := []interface{}{}
    if movieID != nil {
        query += ` AND movie_id = ?`
        args = append(args, *movieID)
    }
    if startTime != nil {
        query += ` AND show_time >= ?`
        args = append(args, *startTime)
    }
    if endTime != nil {
        query += ` AND show_time <= ?`
        args = append(args, *endTime)
    }
    rows, err := r.db.Query(query, args...)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var shows []*domain.Show
    for rows.Next() {
        var s domain.Show
        if err := rows.Scan(&s.ID, &s.MovieID, &s.TheaterID, &s.ShowTime, &s.TotalSeats); err != nil {
            return nil, err
        }
        shows = append(shows, &s)
    }
    return shows, nil
}
''',
        'internal/repository/mysql/seat_repository.go': '''package mysql

import (
    "database/sql"

    "cinema-booking/internal/domain"
)

type SeatRepository struct {
    db *sql.DB
}

func NewSeatRepository(db *sql.DB) *SeatRepository {
    return &SeatRepository{db: db}
}

func (r *SeatRepository) Create(seat *domain.Seat) error {
    query := `INSERT INTO seats (show_id, seat_number, is_booked) VALUES (?, ?, ?)`
    res, err := r.db.Exec(query, seat.ShowID, seat.SeatNumber, seat.IsBooked)
    if err != nil {
        return err
    }
    id, _ := res.LastInsertId()
    seat.ID = int(id)
    return nil
}

func (r *SeatRepository) GetByShowID(showID int) ([]*domain.Seat, error) {
    query := `SELECT id, show_id, seat_number, is_booked FROM seats WHERE show_id = ?`
    rows, err := r.db.Query(query, showID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var seats []*domain.Seat
    for rows.Next() {
        var s domain.Seat
        if err := rows.Scan(&s.ID, &s.ShowID, &s.SeatNumber, &s.IsBooked); err != nil {
            return nil, err
        }
        seats = append(seats, &s)
    }
    return seats, nil
}

func (r *SeatRepository) Update(seat *domain.Seat) error {
    query := `UPDATE seats SET is_booked = ? WHERE id = ?`
    _, err := r.db.Exec(query, seat.IsBooked, seat.ID)
    return err
}
''',
        'internal/repository/mysql/booking_repository.go': '''package mysql

import (
    "database/sql"
    "encoding/json"

    "cinema-booking/internal/domain"
)

type BookingRepository struct {
    db *sql.DB
}

func NewBookingRepository(db *sql.DB) *BookingRepository {
    return &BookingRepository{db: db}
}

func (r *BookingRepository) Create(booking *domain.Booking) error {
    seatIDsJSON, _ := json.Marshal(booking.SeatIDs)
    query := `INSERT INTO bookings (show_id, seat_ids, user_id, user_name, booked_at) VALUES (?, ?, ?, ?, ?)`
    res, err := r.db.Exec(query, booking.ShowID, seatIDsJSON, booking.UserID, booking.UserName, booking.BookedAt)
    if err != nil {
        return err
    }
    id, _ := res.LastInsertId()
    booking.ID = int(id)
    return nil
}

func (r *BookingRepository) ListByShowID(showID int) ([]*domain.Booking, error) {
    query := `SELECT id, show_id, seat_ids, user_name, booked_at FROM bookings WHERE show_id = ?`
    rows, err := r.db.Query(query, showID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var bookings []*domain.Booking
    for rows.Next() {
        var b domain.Booking
        var seatIDsJSON []byte
        if err := rows.Scan(&b.ID, &b.ShowID, &seatIDsJSON, &b.UserName, &b.BookedAt); err != nil {
            return nil, err
        }
        json.Unmarshal(seatIDsJSON, &b.SeatIDs)
        bookings = append(bookings, &b)
    }
    return bookings, nil
}

func (r *BookingRepository) GetByID(id int) (*domain.Booking, error) {
    query := `SELECT id, show_id, seat_ids, user_id, user_name, booked_at FROM bookings WHERE id = ?`
    row := r.db.QueryRow(query, id)
    var b domain.Booking
    var seatIDsJSON []byte
    err := row.Scan(&b.ID, &b.ShowID, &seatIDsJSON, &b.UserID, &b.UserName, &b.BookedAt)
    if err != nil {
        return nil, err
    }
    json.Unmarshal(seatIDsJSON, &b.SeatIDs)
    return &b, nil
}

func (r *BookingRepository) Delete(id int) error {
    query := `DELETE FROM bookings WHERE id = ?`
    _, err := r.db.Exec(query, id)
    return err
}

func (r *BookingRepository) ListByUserID(userID int) ([]*domain.Booking, error) {
    query := `SELECT id, show_id, seat_ids, user_name, booked_at FROM bookings WHERE user_id = ?`
    rows, err := r.db.Query(query, userID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var bookings []*domain.Booking
    for rows.Next() {
        var b domain.Booking
        var seatIDsJSON []byte
        if err := rows.Scan(&b.ID, &b.ShowID, &seatIDsJSON, &b.UserName, &b.BookedAt); err != nil {
            return nil, err
        }
        json.Unmarshal(seatIDsJSON, &b.SeatIDs)
        bookings = append(bookings, &b)
    }
    return bookings, nil
}
''',
        'internal/repository/mysql/user_repository.go': '''package mysql

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
''',
        'internal/repository/mysql/theater_repository.go': '''package mysql

import (
    "database/sql"

    "cinema-booking/internal/domain"
)

type TheaterRepository struct {
    db *sql.DB
}

func NewTheaterRepository(db *sql.DB) *TheaterRepository {
    return &TheaterRepository{db: db}
}

func (r *TheaterRepository) Create(theater *domain.Theater) error {
    query := `INSERT INTO theaters (name, location, capacity) VALUES (?, ?, ?)`
    res, err := r.db.Exec(query, theater.Name, theater.Location, theater.Capacity)
    if err != nil {
        return err
    }
    id, _ := res.LastInsertId()
    theater.ID = int(id)
    return nil
}

func (r *TheaterRepository) GetByID(id int) (*domain.Theater, error) {
    query := `SELECT id, name, location, capacity FROM theaters WHERE id = ?`
    row := r.db.QueryRow(query, id)
    var t domain.Theater
    err := row.Scan(&t.ID, &t.Name, &t.Location, &t.Capacity)
    if err != nil {
        return nil, err
    }
    return &t, nil
}

func (r *TheaterRepository) List() ([]*domain.Theater, error) {
    query := `SELECT id, name, location, capacity FROM theaters`
    rows, err := r.db.Query(query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var theaters []*domain.Theater
    for rows.Next() {
        var t domain.Theater
        if err := rows.Scan(&t.ID, &t.Name, &t.Location, &t.Capacity); err != nil {
            return nil, err
        }
        theaters = append(theaters, &t)
    }
    return theaters, nil
}

func (r *TheaterRepository) Update(theater *domain.Theater) error {
    query := `UPDATE theaters SET name = ?, location = ?, capacity = ? WHERE id = ?`
    _, err := r.db.Exec(query, theater.Name, theater.Location, theater.Capacity, theater.ID)
    return err
}

func (r *TheaterRepository) Delete(id int) error {
    query := `DELETE FROM theaters WHERE id = ?`
    _, err := r.db.Exec(query, id)
    return err
}
''',
        'internal/service/movie_service.go': '''package service

import (
    "cinema-booking/internal/domain"
    "cinema-booking/internal/repository/mysql"
)

type MovieService struct {
    repo *mysql.MovieRepository
}

func NewMovieService(repo *mysql.MovieRepository) *MovieService {
    return &MovieService{repo: repo}
}

func (s *MovieService) CreateMovie(movie *domain.Movie) error {
    if movie.Title == "" {
        return domain.ErrMovieNotFound
    }
    return s.repo.Create(movie)
}

func (s *MovieService) GetMovie(id int) (*domain.Movie, error) {
    return s.repo.GetByID(id)
}

func (s *MovieService) ListMovies() ([]*domain.Movie, error) {
    return s.repo.List()
}
''',
        'internal/service/show_service.go': '''package service

import (
    "time"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/repository/mysql"
)

type ShowService struct {
    repo *mysql.ShowRepository
}

func NewShowService(repo *mysql.ShowRepository) *ShowService {
    return &ShowService{repo: repo}
}

func (s *ShowService) CreateShow(show *domain.Show) error {
    if show.ShowTime.Before(time.Now()) {
        return domain.ErrShowNotFound
    }
    return s.repo.Create(show)
}

func (s *ShowService) GetShow(id int) (*domain.Show, error) {
    return s.repo.GetByID(id)
}

func (s *ShowService) ListShows() ([]*domain.Show, error) {
    return s.repo.List()
}

func (s *ShowService) SearchShows(movieID *int, startTime *time.Time, endTime *time.Time) ([]*domain.Show, error) {
    return s.repo.Search(movieID, startTime, endTime)
}
''',
        'internal/service/seat_service.go': '''package service

import (
    "cinema-booking/internal/domain"
    "cinema-booking/internal/repository/mysql"
)

type SeatService struct {
    repo      *mysql.SeatRepository
    bookingRepo *mysql.BookingRepository
}

func NewSeatService(repo *mysql.SeatRepository, bookingRepo *mysql.BookingRepository) *SeatService {
    return &SeatService{repo: repo, bookingRepo: bookingRepo}
}

func (s *SeatService) GetAvailableSeats(showID int) ([]*domain.Seat, error) {
    seats, err := s.repo.GetByShowID(showID)
    if err != nil {
        return nil, err
    }
    var available []*domain.Seat
    for _, seat := range seats {
        if !seat.IsBooked {
            available = append(available, seat)
        }
    }
    return available, nil
}
''',
        'internal/service/booking_service.go': '''package service

import (
    "encoding/json"
    "time"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/repository/mysql"
)

type BookingService struct {
    seatSvc    *SeatService
    bookingRepo *mysql.BookingRepository
    seatRepo   *mysql.SeatRepository
}

func NewBookingService(seatSvc *SeatService, bookingRepo *mysql.BookingRepository, seatRepo *mysql.SeatRepository) *BookingService {
    return &BookingService{seatSvc: seatSvc, bookingRepo: bookingRepo, seatRepo: seatRepo}
}

func (s *BookingService) BookTickets(req *domain.CreateBookingRequest) (*domain.Booking, error) {
    seats, err := s.seatSvc.GetAvailableSeats(req.ShowID)
    if err != nil {
        return nil, err
    }

    for _, seatID := range req.SeatIDs {
        available := false
        for _, seat := range seats {
            if seat.ID == seatID && !seat.IsBooked {
                available = true
                break
            }
        }
        if !available {
            return nil, domain.ErrSeatNotAvailable
        }
    }

    booking := &domain.Booking{
        ShowID:  req.ShowID,
        SeatIDs: req.SeatIDs,
        UserID:  req.UserID,
        UserName: "User",  // Fetch from user service in prod
        BookedAt: time.Now(),
    }

    tx, err := s.bookingRepo.db.Begin()
    if err != nil {
        return nil, err
    }
    defer tx.Rollback()

    if err := s.bookingRepo.Create(booking); err != nil {
        return nil, err
    }

    for _, seatID := range req.SeatIDs {
        seat := &domain.Seat{ID: seatID, IsBooked: true}
        if err := s.seatRepo.Update(seat); err != nil {
            return nil, err
        }
    }

    if err := tx.Commit(); err != nil {
        return nil, err
    }

    return booking, nil
}

func (s *BookingService) CancelBooking(bookingID int, userID int) error {
    booking, err := s.bookingRepo.GetByID(bookingID)
    if err != nil {
        return domain.ErrBookingNotFound
    }
    if booking.UserID != userID {
        return domain.ErrNotOwner
    }
    for _, seatID := range booking.SeatIDs {
        seat := &domain.Seat{ID: seatID, IsBooked: false}
        if err := s.seatRepo.Update(seat); err != nil {
            return err
        }
    }
    return s.bookingRepo.Delete(bookingID)
}

func (s *BookingService) ListBookingsByUser(userID int) ([]*domain.Booking, error) {
    return s.bookingRepo.ListByUserID(userID)
}
''',
        'internal/service/user_service.go': '''package service

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
''',
        'internal/service/theater_service.go': '''package service

import (
    "cinema-booking/internal/domain"
    "cinema-booking/internal/repository/mysql"
)

type TheaterService struct {
    repo *mysql.TheaterRepository
}

func NewTheaterService(repo *mysql.TheaterRepository) *TheaterService {
    return &TheaterService{repo: repo}
}

func (s *TheaterService) CreateTheater(theater *domain.Theater) error {
    if theater.Name == "" || theater.Capacity <= 0 {
        return domain.ErrTheaterNotFound
    }
    return s.repo.Create(theater)
}

func (s *TheaterService) GetTheater(id int) (*domain.Theater, error) {
    return s.repo.GetByID(id)
}

func (s *TheaterService) ListTheaters() ([]*domain.Theater, error) {
    return s.repo.List()
}

func (s *TheaterService) UpdateTheater(theater *domain.Theater) error {
    return s.repo.Update(theater)
}

func (s *TheaterService) DeleteTheater(id int) error {
    return s.repo.Delete(id)
}
''',
        'internal/handler/http/movie_handler.go': '''package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/service"
)

type MovieHandler struct {
    service *service.MovieService
}

func NewMovieHandler(svc *service.MovieService) *MovieHandler {
    return &MovieHandler{service: svc}
}

func (h *MovieHandler) Create(w http.ResponseWriter, r *http.Request) {
    var movie domain.Movie
    if err := json.NewDecoder(r.Body).Decode(&movie); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    if err := h.service.CreateMovie(&movie); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(movie)
}

func (h *MovieHandler) Get(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])
    movie, err := h.service.GetMovie(id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(movie)
}

func (h *MovieHandler) List(w http.ResponseWriter, r *http.Request) {
    movies, err := h.service.ListMovies()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(movies)
}
''',
        'internal/handler/http/show_handler.go': '''package http

import (
    "encoding/json"
    "net/http"
    "strconv"
    "time"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/service"
)

type ShowHandler struct {
    service *service.ShowService
}

func NewShowHandler(svc *service.ShowService) *ShowHandler {
    return &ShowHandler{service: svc}
}

func (h *ShowHandler) Create(w http.ResponseWriter, r *http.Request) {
    var show domain.Show
    if err := json.NewDecoder(r.Body).Decode(&show); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    if err := time.Parse(time.RFC3339, show.ShowTime.String()); err != nil {
        http.Error(w, "Invalid show time", http.StatusBadRequest)
        return
    }
    if err := h.service.CreateShow(&show); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(show)
}

func (h *ShowHandler) Get(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])
    show, err := h.service.GetShow(id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(show)
}

func (h *ShowHandler) List(w http.ResponseWriter, r *http.Request) {
    shows, err := h.service.ListShows()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(shows)
}

func (h *ShowHandler) Search(w http.ResponseWriter, r *http.Request) {
    movieIDStr := r.URL.Query().Get("movie_id")
    startTimeStr := r.URL.Query().Get("start_time")
    endTimeStr := r.URL.Query().Get("end_time")
    var movieID *int
    var startTime, endTime *time.Time
    if movieIDStr != "" {
        id, _ := strconv.Atoi(movieIDStr)
        movieID = &id
    }
    if startTimeStr != "" {
        t, _ := time.Parse(time.RFC3339, startTimeStr)
        startTime = &t
    }
    if endTimeStr != "" {
        t, _ := time.Parse(time.RFC3339, endTimeStr)
        endTime = &t
    }
    shows, err := h.service.SearchShows(movieID, startTime, endTime)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(shows)
}
''',
        'internal/handler/http/seat_handler.go': '''package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/service"
)

type SeatHandler struct {
    service *service.SeatService
}

func NewSeatHandler(svc *service.SeatService) *SeatHandler {
    return &SeatHandler{service: svc}
}

func (h *SeatHandler) ListAvailable(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    showID, _ := strconv.Atoi(vars["show_id"])
    seats, err := h.service.GetAvailableSeats(showID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(seats)
}
''',
        'internal/handler/http/booking_handler.go': '''package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/middleware"
    "cinema-booking/internal/service"
)

type BookingHandler struct {
    service *service.BookingService
}

func NewBookingHandler(svc *service.BookingService) *BookingHandler {
    return &BookingHandler{service: svc}
}

func (h *BookingHandler) Create(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserIDFromContext(r)
    var req domain.CreateBookingRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    req.UserID = userID
    booking, err := h.service.BookTickets(&req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(booking)
}

func (h *BookingHandler) ListUserBookings(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserIDFromContext(r)
    bookings, err := h.service.ListBookingsByUser(userID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(bookings)
}

func (h *BookingHandler) Cancel(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserIDFromContext(r)
    vars := mux.Vars(r)
    bookingID, _ := strconv.Atoi(vars["id"])
    if err := h.service.CancelBooking(bookingID, userID); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{"message": "Booking cancelled"})
}
''',
        'internal/handler/http/user_handler.go': '''package http

import (
    "encoding/json"
    "net/http"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/service"
)

type UserHandler struct {
    service *service.UserService
}

func NewUserHandler(svc *service.UserService) *UserHandler {
    return &UserHandler{service: svc}
}

func (h *UserHandler) Register(w http.ResponseWriter, r *http.Request) {
    var req domain.RegisterRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    user, err := h.service.Register(&req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}

func (h *UserHandler) Login(w http.ResponseWriter, r *http.Request) {
    var req domain.LoginRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    token, err := h.service.Login(&req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusUnauthorized)
        return
    }
    json.NewEncoder(w).Encode(map[string]string{"token": token})
}
''',
        'internal/handler/http/theater_handler.go': '''package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/service"
)

type TheaterHandler struct {
    service *service.TheaterService
}

func NewTheaterHandler(svc *service.TheaterService) *TheaterHandler {
    return &TheaterHandler{service: svc}
}

func (h *TheaterHandler) Create(w http.ResponseWriter, r *http.Request) {
    var theater domain.Theater
    if err := json.NewDecoder(r.Body).Decode(&theater); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    if err := h.service.CreateTheater(&theater); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(theater)
}

func (h *TheaterHandler) Get(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])
    theater, err := h.service.GetTheater(id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(theater)
}

func (h *TheaterHandler) List(w http.ResponseWriter, r *http.Request) {
    theaters, err := h.service.ListTheaters()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(theaters)
}
''',
        'internal/handler/http/routes.go': '''package http

import (
    "database/sql"
    "log"
    "net/http"

    "github.com/gorilla/mux"

    "cinema-booking/config"
    "cinema-booking/internal/middleware"
    "cinema-booking/internal/repository/mysql"
    "cinema-booking/internal/service"
)

type App struct {
    Router *mux.Router
    cfg    *config.Config
}

func (a *App) Initialize(db *sql.DB, cfg *config.Config) {
    a.cfg = cfg

    movieRepo := mysql.NewMovieRepository(db)
    showRepo := mysql.NewShowRepository(db)
    seatRepo := mysql.NewSeatRepository(db)
    bookingRepo := mysql.NewBookingRepository(db)
    userRepo := mysql.NewUserRepository(db)
    theaterRepo := mysql.NewTheaterRepository(db)

    movieSvc := service.NewMovieService(movieRepo)
    showSvc := service.NewShowService(showRepo)
    seatSvc := service.NewSeatService(seatRepo, bookingRepo)
    bookingSvc := service.NewBookingService(seatSvc, bookingRepo, seatRepo)
    userSvc := service.NewUserService(userRepo, cfg.JWT_SECRET)
    theaterSvc := service.NewTheaterService(theaterRepo)

    movieHandler := NewMovieHandler(movieSvc)
    showHandler := NewShowHandler(showSvc)
    seatHandler := NewSeatHandler(seatSvc)
    bookingHandler := NewBookingHandler(bookingSvc)
    userHandler := NewUserHandler(userSvc)
    theaterHandler := NewTheaterHandler(theaterSvc)

    a.Router = mux.NewRouter()

    // Public routes
    a.Router.HandleFunc("/register", userHandler.Register).Methods("POST")
    a.Router.HandleFunc("/login", userHandler.Login).Methods("POST")
    a.Router.HandleFunc("/movies", movieHandler.List).Methods("GET")
    a.Router.HandleFunc("/movies", movieHandler.Create).Methods("POST")
    a.Router.HandleFunc("/movies/{id}", movieHandler.Get).Methods("GET")
    a.Router.HandleFunc("/shows", showHandler.List).Methods("GET")
    a.Router.HandleFunc("/shows", showHandler.Create).Methods("POST")
    a.Router.HandleFunc("/shows/{id}", showHandler.Get).Methods("GET")
    a.Router.HandleFunc("/shows/{show_id}/seats", seatHandler.ListAvailable).Methods("GET")
    a.Router.HandleFunc("/theaters", theaterHandler.List).Methods("GET")
    a.Router.HandleFunc("/theaters", theaterHandler.Create).Methods("POST")
    a.Router.HandleFunc("/theaters/{id}", theaterHandler.Get).Methods("GET")

    // Protected routes
    auth := middleware.AuthMiddleware(cfg.JWT_SECRET)
    protected := a.Router.PathPrefix("/").Subrouter()
    protected.Use(auth)

    protected.HandleFunc("/shows/search", showHandler.Search).Methods("GET")
    protected.HandleFunc("/bookings", bookingHandler.Create).Methods("POST")
    protected.HandleFunc("/bookings", bookingHandler.ListUserBookings).Methods("GET")
    protected.HandleFunc("/bookings/{id}/cancel", bookingHandler.Cancel).Methods("DELETE")

    a.Router.Use(mux.CORSMethodMiddleware(a.Router))
}

func (a *App) Run(port string) {
    log.Fatal(http.ListenAndServe(":"+port, a.Router))
}
''',
        'internal/middleware/auth.go': '''package middleware

import (
    "context"
    "net/http"
    "strings"

    "github.com/golang-jwt/jwt/v5"
    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
)

type contextKey string

const userIDKey = contextKey("userID")

func AuthMiddleware(secret string) mux.MiddlewareFunc {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            if authHeader == "" {
                http.Error(w, domain.ErrUnauthorized.Error(), http.StatusUnauthorized)
                return
            }
            tokenString := strings.TrimPrefix(authHeader, "Bearer ")
            token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
                return []byte(secret), nil
            })
            if err != nil || !token.Valid {
                http.Error(w, domain.ErrTokenInvalid.Error(), http.StatusUnauthorized)
                return
            }
            claims := token.Claims.(jwt.MapClaims)
            userID := int(claims["user_id"].(float64))
            ctx := context.WithValue(r.Context(), userIDKey, userID)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

func GetUserIDFromContext(r *http.Request) int {
    userID, ok := r.Context().Value(userIDKey).(int)
    if !ok {
        return 0
    }
    return userID
}
'''
    }
}

def create_project():
    root = Path('cinema-booking')
    root.mkdir(exist_ok=True)

    for dir_path, files in project_structure['cinema-booking'].items():
        if dir_path.endswith('.go') or dir_path == '.env' or dir_path == 'go.mod':
            file_path = root / dir_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(files)
        else:
            # For subdirs like internal/handler/http
            sub_dir = root / dir_path
            sub_dir.mkdir(parents=True, exist_ok=True)

    print("Project files created in 'cinema-booking/'")

def zip_project():
    zip_path = Path('cinema-booking.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root_dir, dirs, files in os.walk('cinema-booking'):
            for file in files:
                file_path = os.path.join(root_dir, file)
                arcname = os.path.relpath(file_path, 'cinema-booking')
                zipf.write(file_path, arcname)
    print(f"Project zipped as '{zip_path}'")

if __name__ == "__main__":
    create_project()
    zip_project()
