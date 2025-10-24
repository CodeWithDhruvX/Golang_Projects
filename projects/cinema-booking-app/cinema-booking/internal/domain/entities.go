package domain

import "time"

type Movie struct {
    ID          int       `json:"id"`
    Title       string    `json:"title"`
    Duration    int       `json:"duration_minutes"`
    Genre       string    `json:"genre"`
}

type Show struct {
    ID          int       `json:"id"`
    MovieID     int       `json:"movie_id"`
    TheaterID   int       `json:"theater_id"`
    ShowTime    time.Time `json:"show_time"`
    TotalSeats  int       `json:"total_seats"`
}

type Seat struct {
    ID        int `json:"id"`
    ShowID    int `json:"show_id"`
    SeatNumber string `json:"seat_number"`
    IsBooked  bool    `json:"is_booked"`
}

type Booking struct {
    ID      int       `json:"id"`
    ShowID  int       `json:"show_id"`
    SeatIDs []int     `json:"seat_ids"`
    UserID  int       `json:"user_id"`
    UserName string   `json:"user_name"`
    BookedAt time.Time `json:"booked_at"`
}

type User struct {
    ID       int    `json:"id"`
    Username string `json:"username"`
    Email    string `json:"email"`
    Password string `json:"-"`  // Not exposed
}

type Theater struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
    Location string `json:"location"`
    Capacity int `json:"capacity"`
}

type LoginRequest struct {
    Email    string `json:"email"`
    Password string `json:"password"`
}

type RegisterRequest struct {
    Username string `json:"username"`
    Email    string `json:"email"`
    Password string `json:"password"`
}

type CreateBookingRequest struct {
    ShowID  int      `json:"show_id"`
    SeatIDs []int    `json:"seat_ids"`
    UserID  int      `json:"user_id"`
}

type CancelBookingRequest struct {
    BookingID int `json:"booking_id"`
}
