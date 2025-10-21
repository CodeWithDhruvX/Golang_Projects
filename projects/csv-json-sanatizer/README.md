# CSV/JSON Data Sanitizer

A Go CLI tool for cleaning and validating CSV/JSON data files.

## Setup
1. `go mod tidy`
2. Build: `go build -o sanitizer ./cmd/sanitizer`

## Usage
`./sanitizer -input data.csv -output cleaned.json -rules configs/rules.yaml`

Supports trimming, validation (e.g., email), duplicate removal, and CSV injection escaping.


https://www.perplexity.ai/search/goal-i-have-built-an-app-with-oGCFH3MRQIitnsN1ezjwnA