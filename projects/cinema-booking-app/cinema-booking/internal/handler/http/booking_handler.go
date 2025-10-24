package http

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
    "cinema-booking/internal/middleware"
    "cinema-booking/internal/service"
)

type BookingHandler struct {
    service *service.BookingService
}

func NewBookingHandler(svc *service.BookingService) *BookingHandler {
    return &BookingHandler{service: svc}
}

func (h *BookingHandler) Create(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserIDFromContext(r)
    var req domain.CreateBookingRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    req.UserID = userID
    booking, err := h.service.BookTickets(&req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(booking)
}

func (h *BookingHandler) ListUserBookings(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserIDFromContext(r)
    bookings, err := h.service.ListBookingsByUser(userID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(bookings)
}

func (h *BookingHandler) Cancel(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserIDFromContext(r)
    vars := mux.Vars(r)
    bookingID, _ := strconv.Atoi(vars["id"])
    if err := h.service.CancelBooking(bookingID, userID); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{"message": "Booking cancelled"})
}
