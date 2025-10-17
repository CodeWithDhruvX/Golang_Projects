package http

import (
	"it-setup-service/domain"
	"it-setup-service/usecase"
	"net/http"

	"github.com/gin-gonic/gin"
)

type provisionHandler struct {
	usecase usecase.ProvisionUsecase
}

func NewProvisionHandler(usecase usecase.ProvisionUsecase) *provisionHandler {
	return &provisionHandler{usecase: usecase}
}

func (h *provisionHandler) Provision(c *gin.Context) {
	var req domain.ProvisionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	prov, err := h.usecase.Provision(c.Request.Context(), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, prov)
}
