package infrastructure

import (
	"fmt"
	"os"
)

// SaveFile stores binary data to a file
func SaveFile(filename string, data []byte) error {
	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("failed to create file: %v", err)
	}
	defer file.Close()

	_, err = file.Write(data)
	if err != nil {
		return fmt.Errorf("failed to write file: %v", err)
	}
	return nil
}
