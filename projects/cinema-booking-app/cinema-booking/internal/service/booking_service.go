package service

import (
	"database/sql" // Add this import for *sql.Tx and *sql.DB
	"time"

	"cinema-booking/internal/domain"
	"cinema-booking/internal/repository/mysql"
)

type BookingService struct {
	seatSvc     *SeatService
	bookingRepo *mysql.BookingRepository
	seatRepo    *mysql.SeatRepository
	db          *sql.DB // Keep for starting tx
}

func NewBookingService(seatSvc *SeatService, bookingRepo *mysql.BookingRepository, seatRepo *mysql.SeatRepository, db *sql.DB) *BookingService {
	return &BookingService{seatSvc: seatSvc, bookingRepo: bookingRepo, seatRepo: seatRepo, db: db}
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
		ShowID:   req.ShowID,
		SeatIDs:  req.SeatIDs,
		UserID:   req.UserID,
		UserName: "User", // Fetch from user service in prod
		BookedAt: time.Now(),
	}

	tx, err := s.db.Begin()
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()

	if err := s.bookingRepo.Create(booking, tx); err != nil { // Pass tx (nil-safe in repo)
		return nil, err
	}

	for _, seatID := range req.SeatIDs {
		seat := &domain.Seat{ID: seatID, IsBooked: true}
		if err := s.seatRepo.Update(seat, tx); err != nil { // Pass tx
			return nil, err
		}
	}

	if err := tx.Commit(); err != nil {
		return nil, err
	}

	return booking, nil
}

func (s *BookingService) CancelBooking(bookingID int, userID int) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	booking, err := s.bookingRepo.GetByID(bookingID, tx) // Pass tx
	if err != nil {
		return domain.ErrBookingNotFound
	}
	if booking.UserID != userID {
		return domain.ErrNotOwner
	}

	for _, seatID := range booking.SeatIDs {
		seat := &domain.Seat{ID: seatID, IsBooked: false}
		if err := s.seatRepo.Update(seat, tx); err != nil {
			return err
		}
	}

	if err := s.bookingRepo.Delete(bookingID, tx); err != nil {
		return err
	}

	return tx.Commit()
}

func (s *BookingService) ListBookingsByUser(userID int) ([]*domain.Booking, error) {
	return s.bookingRepo.ListByUserID(userID, nil) // No tx needed for list
}
