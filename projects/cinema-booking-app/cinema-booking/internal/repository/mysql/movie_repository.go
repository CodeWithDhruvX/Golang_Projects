package mysql

import (
	"database/sql"

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
