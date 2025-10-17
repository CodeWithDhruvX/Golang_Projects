package http

import (
	"hr-service/domain"
	"hr-service/usecase"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

type employeeHandler struct {
	usecase usecase.EmployeeUsecase
}

func NewEmployeeHandler(usecase usecase.EmployeeUsecase) *employeeHandler {
	return &employeeHandler{usecase: usecase}
}

func (h *employeeHandler) Onboard(c *gin.Context) {
	var req domain.OnboardingRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	emp, err := h.usecase.Onboard(c.Request.Context(), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, emp)
}

func (h *employeeHandler) GetByID(c *gin.Context) {
	idStr := c.Param("id")
	id, _ := strconv.Atoi(idStr)
	emp, err := h.usecase.GetByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Not found"})
		return
	}
	c.JSON(http.StatusOK, emp)
}
