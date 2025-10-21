package utils

import (
	"regexp"
	"strings"

	"csv-json-sanitizer/internal/domain"
)

var emailRegex = regexp.MustCompile(`^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,4}$`)

// CleanValue applies sanitization based on rule.
func CleanValue(val string, rule domain.SanitizationRule) string {
	// Trim whitespace
	val = strings.TrimSpace(val)

	// Handle empty/missing
	if val == "" && rule.Default != "" {
		return rule.Default
	}

	// Apply action-specific sanitization
	if rule.Action == "escape" {
		// CSV injection escape: prefix dangerous chars with space
		if strings.HasPrefix(val, "=") || strings.HasPrefix(val, "+") || strings.HasPrefix(val, "-") || strings.HasPrefix(val, "@") {
			val = " " + val
		}
	}

	// Validate based on type (if validator present)
	if rule.Validator == "email" && !emailRegex.MatchString(val) {
		return "" // Invalid, return empty
	}

	return val
}
