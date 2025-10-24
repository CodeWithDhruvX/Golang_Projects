# qr_code_generator

Complete Go implementation of a QR code generator demonstrating:
- Factory Method pattern
- Thread-safe map cache
- PostgreSQL integration with GORM
- Standard, Custom and Batch QR generators
- QR scanner (using tuotoo/qrcode)


https://chatgpt.com/c/68c916d1-a1fc-8323-8b24-3da67e29af4b


go run cmd/main.go generate "Hello from Standard QR"

go run cmd/main.go batch data.json json   

go run cmd/main.go batch data.csv csv   

go run cmd/main.go custom "Hello Colored QR" blue


