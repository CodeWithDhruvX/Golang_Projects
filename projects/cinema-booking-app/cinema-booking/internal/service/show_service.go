package service

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
