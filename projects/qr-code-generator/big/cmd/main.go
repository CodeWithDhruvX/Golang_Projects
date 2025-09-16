package main

import (
	api "example.com/big/api/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	// f := &factory.QRCodeFactory{}

	// // Example 1: Text QR Code
	// textQR, err := f.Create("text", "Hello, Production QR!")
	// if err != nil {
	// 	fmt.Println("Error creating QR code:", err)
	// 	os.Exit(1)
	// }
	// err = textQR.Generate("text_qr.png")
	// if err != nil {

	// 	fmt.Println("Error generating QR code:", err)
	// 	os.Exit(1)
	// }

	// // Example 2: URL QR Code
	// urlQR, err := f.Create("url", "https://github.com/CodeWithDhruvX")
	// if err != nil {
	// 	fmt.Println("Error creating QR code:", err)
	// 	os.Exit(1)
	// }
	// err = urlQR.Generate("url_qr.png")
	// if err != nil {
	// 	fmt.Println("Error generating QR code:", err)
	// 	os.Exit(1)
	// }

	// fmt.Println("QR Codes generated successfully!")

	r := gin.Default()

	// Register QR code generation routes
	api.RegisterRoutes(r)

	// Start the server on port 8080
	r.Run(":8080") // accessible at http://localhost:8080
}
