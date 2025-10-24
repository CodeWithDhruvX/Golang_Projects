package service

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
