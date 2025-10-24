package mysql

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

func (r *SeatRepository) Update(seat *domain.Seat, tx *sql.Tx) error {
	query := `UPDATE seats SET is_booked = ? WHERE id = ?`
	if tx != nil {
		_, err := tx.Exec(query, seat.IsBooked, seat.ID)
		return err
	}
	_, err := r.db.Exec(query, seat.IsBooked, seat.ID)
	return err
}
