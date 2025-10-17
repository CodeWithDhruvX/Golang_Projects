package http

import (
	"email-provisioner-service/domain"
	"email-provisioner-service/usecase"
	"net/http"

	"github.com/gin-gonic/gin"
)

type emailHandler struct {
	usecase usecase.EmailUsecase
}

func NewEmailHandler(usecase usecase.EmailUsecase) *emailHandler {
	return &emailHandler{usecase: usecase}
}

func (h *emailHandler) Send(c *gin.Context) {
	var req domain.SendRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	log, err := h.usecase.Send(c.Request.Context(), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, log)
}
