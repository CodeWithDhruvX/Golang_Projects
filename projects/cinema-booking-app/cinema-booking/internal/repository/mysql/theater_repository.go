package mysql

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
