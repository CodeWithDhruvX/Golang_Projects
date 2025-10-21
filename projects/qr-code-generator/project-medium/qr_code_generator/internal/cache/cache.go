package cache

import (
	"crypto/sha256"
	"encoding/hex"
	"qr_code_generator/internal/models"
	"sync"
)

// thread-safe hash table cache
var mu sync.RWMutex
var qrCache = make(map[string]models.QRRecord)

// hash function for consistent keys
func hash(data string) string {
	h := sha256.Sum256([]byte(data))
	return hex.EncodeToString(h[:])
}

func AddToCache(data string, record models.QRRecord) {
	mu.Lock()
	defer mu.Unlock()
	qrCache[hash(data)] = record
}

func GetFromCache(data string) (models.QRRecord, bool) {
	mu.RLock()
	defer mu.RUnlock()
	rec, found := qrCache[hash(data)]
	return rec, found
}

// ClearCache deletes all cached QR records
func ClearCache() {
	for k := range qrCache {
		delete(qrCache, k)
	}
}
