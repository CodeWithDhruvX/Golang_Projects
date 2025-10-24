package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/service"
)

type SeatHandler struct {
    service *service.SeatService
}

func NewSeatHandler(svc *service.SeatService) *SeatHandler {
    return &SeatHandler{service: svc}
}

func (h *SeatHandler) ListAvailable(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    showID, _ := strconv.Atoi(vars["show_id"])
    seats, err := h.service.GetAvailableSeats(showID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(seats)
}
