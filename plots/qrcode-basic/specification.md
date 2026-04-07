# qrcode-basic: Basic QR Code Generator

## Description

A QR (Quick Response) code visualization that encodes text or URL data into a square matrix barcode pattern. QR codes are two-dimensional barcodes that store information in a grid of black and white squares, readable by smartphones and dedicated scanners. This visualization is useful for generating scannable codes for quick data sharing and mobile access.

## Applications

- Encoding URLs for easy mobile website access via smartphone camera
- Generating WiFi network credentials for quick device connection
- Creating vCard contact information for instant address book import
- Event ticket and badge generation for access control
- Product identification and inventory tracking

## Data

- `content` (string) - The text, URL, or data to encode in the QR code
- `error_correction` (string) - Error correction level: L (7%), M (15%), Q (25%), H (30%)
- Size: Single input string, typically up to 4,296 alphanumeric characters
- Example: "https://pyplots.ai" or "BEGIN:VCARD\nVERSION:3.0\nN:Doe;John..."

## Notes

- Include a quiet zone (white border) around the QR code for reliable scanning
- Use high contrast black on white for maximum readability
- Position detection patterns (finder patterns) in three corners are required
- Recommended libraries: `qrcode` (primary, with PIL for rendering), `segno`, or `pyqrcode`
- Output should be printable at 300 DPI for physical media
- Error correction level M (15%) is a good default balance between capacity and reliability
- The generated QR code MUST be scannable by standard QR code readers — use a proper QR encoding library (`qrcode` is the primary recommendation) instead of manually constructing the QR matrix
