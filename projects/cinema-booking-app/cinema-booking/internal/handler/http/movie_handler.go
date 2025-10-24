package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/service"
)

type MovieHandler struct {
    service *service.MovieService
}

func NewMovieHandler(svc *service.MovieService) *MovieHandler {
    return &MovieHandler{service: svc}
}

func (h *MovieHandler) Create(w http.ResponseWriter, r *http.Request) {
    var movie domain.Movie
    if err := json.NewDecoder(r.Body).Decode(&movie); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    if err := h.service.CreateMovie(&movie); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(movie)
}

func (h *MovieHandler) Get(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])
    movie, err := h.service.GetMovie(id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(movie)
}

func (h *MovieHandler) List(w http.ResponseWriter, r *http.Request) {
    movies, err := h.service.ListMovies()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(movies)
}
