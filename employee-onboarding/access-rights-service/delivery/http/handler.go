package http

import (
	"access-rights-service/domain"
	"access-rights-service/usecase"
	"net/http"

	"github.com/gin-gonic/gin"
)

type accessHandler struct {
	usecase usecase.AccessUsecase
}

func NewAccessHandler(usecase usecase.AccessUsecase) *accessHandler {
	return &accessHandler{usecase: usecase}
}

func (h *accessHandler) Grant(c *gin.Context) {
	var req domain.GrantRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	grant, err := h.usecase.Grant(c.Request.Context(), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, grant)
}
