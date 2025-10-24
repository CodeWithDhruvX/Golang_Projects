package middleware

import (
    "context"
    "net/http"
    "strings"

    "github.com/golang-jwt/jwt/v5"
    "github.com/gorilla/mux"

    "cinema-booking/internal/domain"
)

type contextKey string

const userIDKey = contextKey("userID")

func AuthMiddleware(secret string) mux.MiddlewareFunc {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            if authHeader == "" {
                http.Error(w, domain.ErrUnauthorized.Error(), http.StatusUnauthorized)
                return
            }
            tokenString := strings.TrimPrefix(authHeader, "Bearer ")
            token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
                return []byte(secret), nil
            })
            if err != nil || !token.Valid {
                http.Error(w, domain.ErrTokenInvalid.Error(), http.StatusUnauthorized)
                return
            }
            claims := token.Claims.(jwt.MapClaims)
            userID := int(claims["user_id"].(float64))
            ctx := context.WithValue(r.Context(), userIDKey, userID)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

func GetUserIDFromContext(r *http.Request) int {
    userID, ok := r.Context().Value(userIDKey).(int)
    if !ok {
        return 0
    }
    return userID
}
