package domain

import "errors"

var (
    ErrMovieNotFound = errors.New("movie not found")
    ErrShowNotFound  = errors.New("show not found")
    ErrSeatNotAvailable = errors.New("seat not available")
    ErrBookingFailed    = errors.New("booking failed")
    ErrUserNotFound     = errors.New("user not found")
    ErrInvalidCredentials = errors.New("invalid email or password")
    ErrTokenInvalid     = errors.New("invalid token")
    ErrUnauthorized     = errors.New("unauthorized access")
    ErrBookingNotFound  = errors.New("booking not found")
    ErrNotOwner         = errors.New("not the booking owner")
    ErrTheaterNotFound  = errors.New("theater not found")
)
