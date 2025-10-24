package service

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
