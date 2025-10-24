package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/service"
)

type TheaterHandler struct {
    service *service.TheaterService
}

func NewTheaterHandler(svc *service.TheaterService) *TheaterHandler {
    return &TheaterHandler{service: svc}
}

func (h *TheaterHandler) Create(w http.ResponseWriter, r *http.Request) {
    var theater domain.Theater
    if err := json.NewDecoder(r.Body).Decode(&theater); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    if err := h.service.CreateTheater(&theater); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(theater)
}

func (h *TheaterHandler) Get(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])
    theater, err := h.service.GetTheater(id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(theater)
}

func (h *TheaterHandler) List(w http.ResponseWriter, r *http.Request) {
    theaters, err := h.service.ListTheaters()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(theaters)
}
