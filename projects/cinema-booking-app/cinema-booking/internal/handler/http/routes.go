package http

import (
	"database/sql"
	"log"
	"net/http"

	"github.com/gorilla/mux"

	"cinema-booking/config"
	"cinema-booking/internal/middleware"
	"cinema-booking/internal/repository/mysql"
	"cinema-booking/internal/service"
)

type App struct {
	Router *mux.Router
	cfg    *config.Config
}

func (a *App) Initialize(db *sql.DB, cfg *config.Config) {
	a.cfg = cfg

	movieRepo := mysql.NewMovieRepository(db)
	showRepo := mysql.NewShowRepository(db)
	seatRepo := mysql.NewSeatRepository(db)
	bookingRepo := mysql.NewBookingRepository(db)
	userRepo := mysql.NewUserRepository(db)
	theaterRepo := mysql.NewTheaterRepository(db)

	movieSvc := service.NewMovieService(movieRepo)
	showSvc := service.NewShowService(showRepo)
	seatSvc := service.NewSeatService(seatRepo, bookingRepo)
	// In Initialize, after repos:
	bookingSvc := service.NewBookingService(seatSvc, bookingRepo, seatRepo, db) // Pass db here
	// Other services don't need tx, so unchanged

	userSvc := service.NewUserService(userRepo, cfg.JWT_SECRET)
	theaterSvc := service.NewTheaterService(theaterRepo)

	movieHandler := NewMovieHandler(movieSvc)
	showHandler := NewShowHandler(showSvc)
	seatHandler := NewSeatHandler(seatSvc)
	bookingHandler := NewBookingHandler(bookingSvc)
	userHandler := NewUserHandler(userSvc)
	theaterHandler := NewTheaterHandler(theaterSvc)

	a.Router = mux.NewRouter()

	// Public routes
	a.Router.HandleFunc("/register", userHandler.Register).Methods("POST")
	a.Router.HandleFunc("/login", userHandler.Login).Methods("POST")
	a.Router.HandleFunc("/movies", movieHandler.List).Methods("GET")
	a.Router.HandleFunc("/movies", movieHandler.Create).Methods("POST")
	a.Router.HandleFunc("/movies/{id}", movieHandler.Get).Methods("GET")
	a.Router.HandleFunc("/shows", showHandler.List).Methods("GET")
	a.Router.HandleFunc("/shows", showHandler.Create).Methods("POST")
	a.Router.HandleFunc("/shows/{id}", showHandler.Get).Methods("GET")
	a.Router.HandleFunc("/shows/{show_id}/seats", seatHandler.ListAvailable).Methods("GET")
	a.Router.HandleFunc("/theaters", theaterHandler.List).Methods("GET")
	a.Router.HandleFunc("/theaters", theaterHandler.Create).Methods("POST")
	a.Router.HandleFunc("/theaters/{id}", theaterHandler.Get).Methods("GET")

	// Protected routes
	auth := middleware.AuthMiddleware(cfg.JWT_SECRET)
	protected := a.Router.PathPrefix("/").Subrouter()
	protected.Use(auth)

	protected.HandleFunc("/shows/search", showHandler.Search).Methods("GET")
	protected.HandleFunc("/bookings", bookingHandler.Create).Methods("POST")
	protected.HandleFunc("/bookings", bookingHandler.ListUserBookings).Methods("GET")
	protected.HandleFunc("/bookings/{id}/cancel", bookingHandler.Cancel).Methods("DELETE")

	a.Router.Use(mux.CORSMethodMiddleware(a.Router))
}

func (a *App) Run(port string) {
	log.Fatal(http.ListenAndServe(":"+port, a.Router))
}
