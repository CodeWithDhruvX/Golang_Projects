package usecase

import (
	"fmt"
	"strings"
	"time"

	"csv-json-sanitizer/internal/domain"
	"csv-json-sanitizer/pkg/utils"
)

type SanitizeService struct{}

func NewSanitizeService() domain.SanitizerPort {
	return &SanitizeService{}
}

func (s *SanitizeService) Sanitize(rows []domain.Row, rules []domain.SanitizationRule) ([]domain.Row, domain.SanitizationResult) {
	result := domain.SanitizationResult{
		Processed: len(rows),
		Timestamp: time.Now(),
	}

	cleaned := make([]domain.Row, 0, len(rows))
	seen := make(map[string]bool) // For duplicate detection via key hash

	for _, row := range rows {
		// Apply rules
		for _, rule := range rules {
			if val, exists := row[rule.Field]; exists {
				cleanedVal := utils.CleanValue(fmt.Sprintf("%v", val), rule)
				row[rule.Field] = cleanedVal

				if rule.Required && cleanedVal == "" {
					result.Errors++
					continue // Skip invalid rows
				}
				row[rule.Field] = cleanedVal
			} else if rule.Required {
				row[rule.Field] = rule.Default
				result.Errors++
			}
		}

		// Check duplicates (simple hash of all fields)
		key := s.rowKey(row)
		if seen[key] {
			result.Duplicates++
			continue
		}
		seen[key] = true

		cleaned = append(cleaned, row)
	}

	return cleaned, result
}

func (s *SanitizeService) rowKey(row domain.Row) string {
	var keys []string
	for k := range row {
		keys = append(keys, fmt.Sprintf("%s:%v", k, row[k]))
	}
	return strings.Join(keys, "|")
}
