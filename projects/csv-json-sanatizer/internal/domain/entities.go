package domain

import "time"

// Row represents a single data row from CSV or JSON.
type Row map[string]interface{}

// SanitizationRule defines configurable cleaning rules.
type SanitizationRule struct {
	Field     string `yaml:"field"`
	Required  bool   `yaml:"required"`
	Default   string `yaml:"default,omitempty"`
	Validator string `yaml:"validator,omitempty"` // e.g., "email"
	Action    string `yaml:"action,omitempty"`    // e.g., "escape"
}

// SanitizationResult holds processing outcomes.
type SanitizationResult struct {
	Processed  int       `json:"processed"`
	Errors     int       `json:"errors"`
	Duplicates int       `json:"duplicates_removed"`
	Timestamp  time.Time `json:"timestamp"`
}

// SanitizerPort defines the interface for sanitization logic.
type SanitizerPort interface {
	Sanitize([]Row, []SanitizationRule) ([]Row, SanitizationResult)
}
