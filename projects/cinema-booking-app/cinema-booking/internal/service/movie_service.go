package service

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
