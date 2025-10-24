package mysql

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

func (r *BookingRepository) Create(booking *domain.Booking, tx *sql.Tx) error {
	seatIDsJSON, err := json.Marshal(booking.SeatIDs)
	if err != nil {
		return err
	}
	query := `INSERT INTO bookings (show_id, seat_ids, user_id, user_name, booked_at) VALUES (?, ?, ?, ?, ?)`
	var res sql.Result
	var execErr error
	if tx != nil {
		res, execErr = tx.Exec(query, booking.ShowID, seatIDsJSON, booking.UserID, booking.UserName, booking.BookedAt)
	} else {
		res, execErr = r.db.Exec(query, booking.ShowID, seatIDsJSON, booking.UserID, booking.UserName, booking.BookedAt)
	}
	if execErr != nil {
		return execErr
	}
	id, _ := res.LastInsertId()
	booking.ID = int(id)
	return nil
}

func (r *BookingRepository) GetByID(id int, tx *sql.Tx) (*domain.Booking, error) {
	query := `SELECT id, show_id, seat_ids, user_id, user_name, booked_at FROM bookings WHERE id = ?`
	var row *sql.Row
	if tx != nil {
		row = tx.QueryRow(query, id)
	} else {
		row = r.db.QueryRow(query, id)
	}
	var b domain.Booking
	var seatIDsJSON []byte
	err := row.Scan(&b.ID, &b.ShowID, &seatIDsJSON, &b.UserID, &b.UserName, &b.BookedAt)
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(seatIDsJSON, &b.SeatIDs); err != nil {
		return nil, err
	}
	return &b, nil
}

func (r *BookingRepository) Delete(id int, tx *sql.Tx) error {
	query := `DELETE FROM bookings WHERE id = ?`
	if tx != nil {
		_, err := tx.Exec(query, id)
		return err
	}
	_, err := r.db.Exec(query, id)
	return err
}

func (r *BookingRepository) ListByUserID(userID int, tx *sql.Tx) ([]*domain.Booking, error) {
	query := `SELECT id, show_id, seat_ids, user_id, user_name, booked_at FROM bookings WHERE user_id = ?`
	var rows *sql.Rows
	var queryErr error
	if tx != nil {
		rows, queryErr = tx.Query(query, userID)
	} else {
		rows, queryErr = r.db.Query(query, userID)
	}
	if queryErr != nil {
		return nil, queryErr
	}
	defer rows.Close()

	var bookings []*domain.Booking
	for rows.Next() {
		var b domain.Booking
		var seatIDsJSON []byte
		if err := rows.Scan(&b.ID, &b.ShowID, &seatIDsJSON, &b.UserID, &b.UserName, &b.BookedAt); err != nil {
			return nil, err
		}
		if err := json.Unmarshal(seatIDsJSON, &b.SeatIDs); err != nil {
			return nil, err
		}
		bookings = append(bookings, &b)
	}
	return bookings, nil
}

func (r *BookingRepository) ListByShowID(showID int) ([]*domain.Booking, error) {
	// Legacy non-tx method
	query := `SELECT id, show_id, seat_ids, user_id, user_name, booked_at FROM bookings WHERE show_id = ?`
	rows, err := r.db.Query(query, showID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var bookings []*domain.Booking
	for rows.Next() {
		var b domain.Booking
		var seatIDsJSON []byte
		if err := rows.Scan(&b.ID, &b.ShowID, &seatIDsJSON, &b.UserID, &b.UserName, &b.BookedAt); err != nil {
			return nil, err
		}
		if err := json.Unmarshal(seatIDsJSON, &b.SeatIDs); err != nil {
			return nil, err
		}
		bookings = append(bookings, &b)
	}
	return bookings, nil
}
