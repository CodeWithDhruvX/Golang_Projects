package httpclient

import (
    "bytes"
    "context"
    "encoding/json"
    "net/http"
)

type Client struct {
    BaseURL string
}

func NewClient(baseURL string) *Client {
    return &Client{BaseURL: baseURL}
}

func (c *Client) Post(ctx context.Context, path string, payload interface{}) (*http.Response, error) {
    data, _ := json.Marshal(payload)
    req, err := http.NewRequestWithContext(ctx, "POST", c.BaseURL+path, bytes.NewBuffer(data))
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", "application/json")
    return http.DefaultClient.Do(req)
}
