package repository

import (
    "encoding/csv"
    "encoding/json"
    "fmt"
    "io"
    "os"
    "path/filepath"
    "strings"

    "csv-json-sanitizer/internal/domain"
)

type FileHandler struct{}

func NewFileHandler() *FileHandler {
    return &FileHandler{}
}

// ReadFile reads CSV or JSON into rows.
func (h *FileHandler) ReadFile(path string) ([]domain.Row, error) {
    ext := strings.ToLower(filepath.Ext(path))
    file, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer file.Close()

    if ext == ".csv" {
        return h.readCSV(file)
    } else if ext == ".json" {
        return h.readJSON(file)
    }
    return nil, domain.ErrInvalidFile
}

func (h *FileHandler) readCSV(r io.Reader) ([]domain.Row, error) {
    reader := csv.NewReader(r)
    records, err := reader.ReadAll()
    if err != nil {
        return nil, err
    }

    if len(records) == 0 {
        return []domain.Row{}, nil
    }

    headers := records[0]
    rows := make([]domain.Row, 0, len(records)-1)
    for _, record := range records[1:] {
        row := make(domain.Row)
        for i, val := range record {
            if i < len(headers) {
                row[headers[i]] = strings.TrimSpace(val)
            }
        }
        rows = append(rows, row)
    }
    return rows, nil
}

func (h *FileHandler) readJSON(r io.Reader) ([]domain.Row, error) {
    var data []domain.Row
    if err := json.NewDecoder(r).Decode(&data); err != nil {
        return nil, err
    }
    return data, nil
}

// WriteFile writes rows to CSV or JSON.
func (h *FileHandler) WriteFile(path string, rows []domain.Row, result domain.SanitizationResult) error {
    file, err := os.Create(path)
    if err != nil {
        return err
    }
    defer file.Close()

    ext := strings.ToLower(filepath.Ext(path))
    if ext == ".csv" {
        return h.writeCSV(file, rows)
    } else if ext == ".json" {
        return h.writeJSON(file, rows, result)
    }
    return domain.ErrInvalidFile
}

func (h *FileHandler) writeCSV(w io.Writer, rows []domain.Row) error {
    writer := csv.NewWriter(w)
    defer writer.Flush()

    // Assume rows have consistent keys; get headers from first row
    if len(rows) == 0 {
        return nil
    }

    headers := make([]string, 0)
    for k := range rows[0] {
        headers = append(headers, k)
    }
    if err := writer.Write(headers); err != nil {
        return err
    }

    for _, row := range rows {
        record := make([]string, len(headers))
        for i, h := range headers {
            if val, ok := row[h]; ok {
                record[i] = fmt.Sprintf("%v", val)
            }
        }
        if err := writer.Write(record); err != nil {
            return err
        }
    }
    return nil
}

func (h *FileHandler) writeJSON(w io.Writer, rows []domain.Row, result domain.SanitizationResult) error {
    output := struct {
        Data   []domain.Row          `json:"data"`
        Result domain.SanitizationResult `json:"result"`
    }{rows, result}

    return json.NewEncoder(w).Encode(output)
}