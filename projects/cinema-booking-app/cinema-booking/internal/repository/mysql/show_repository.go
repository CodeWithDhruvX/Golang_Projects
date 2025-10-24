package mysql

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
