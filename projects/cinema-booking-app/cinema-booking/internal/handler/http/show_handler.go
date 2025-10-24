package http

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/gorilla/mux"

	"cinema-booking/internal/domain"
	"cinema-booking/internal/service"
)

type ShowHandler struct {
	service *service.ShowService
}

func NewShowHandler(svc *service.ShowService) *ShowHandler {
	return &ShowHandler{service: svc}
}

func (h *ShowHandler) Create(w http.ResponseWriter, r *http.Request) {
	var show domain.Show
	if err := json.NewDecoder(r.Body).Decode(&show); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	// JSON decode validates RFC3339 for time.Time; service checks future time
	if err := h.service.CreateShow(&show); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(show)
}

func (h *ShowHandler) Get(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, _ := strconv.Atoi(vars["id"])
	show, err := h.service.GetShow(id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(show)
}

func (h *ShowHandler) List(w http.ResponseWriter, r *http.Request) {
	shows, err := h.service.ListShows()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(shows)
}

func (h *ShowHandler) Search(w http.ResponseWriter, r *http.Request) {
	movieIDStr := r.URL.Query().Get("movie_id")
	startTimeStr := r.URL.Query().Get("start_time")
	endTimeStr := r.URL.Query().Get("end_time")
	var movieID *int
	var startTime, endTime *time.Time
	if movieIDStr != "" {
		id, _ := strconv.Atoi(movieIDStr)
		movieID = &id
	}
	if startTimeStr != "" {
		t, err := time.Parse(time.RFC3339, startTimeStr)
		if err == nil {
			startTime = &t
		}
		// Ignore invalid parse for optional param; in prod, return 400
	}
	if endTimeStr != "" {
		t, err := time.Parse(time.RFC3339, endTimeStr)
		if err == nil {
			endTime = &t
		}
		// Ignore invalid parse
	}
	shows, err := h.service.SearchShows(movieID, startTime, endTime)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(shows)
}
