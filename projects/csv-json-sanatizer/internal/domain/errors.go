package domain

import "errors"

var (
    ErrInvalidFile    = errors.New("invalid input file format")
    ErrMissingField   = errors.New("required field is missing")
    ErrValidationFail = errors.New("validation failed for field")
    ErrDuplicateRow   = errors.New("duplicate row detected")
)