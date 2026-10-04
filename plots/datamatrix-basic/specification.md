# datamatrix-basic: Basic Data Matrix 2D Barcode

## Description

A Data Matrix 2D barcode visualization that encodes data into a compact square or rectangular matrix of black and white cells. Data Matrix codes follow the ISO/IEC 16022 standard, featuring an L-shaped finder pattern (solid borders on two adjacent sides) and alternating timing patterns on the opposite sides. This barcode format is ideal for marking small items and supports high data density with built-in error correction (ECC 200).

## Applications

- Small item marking for electronics, medical devices, and aerospace components
- Document management and archival tracking systems
- Industrial parts identification and manufacturing traceability
- Postal services for mail sorting and tracking
- Pharmaceutical serialization for drug authentication and supply chain security

## Data

- `content` (string) - The text, alphanumeric, or binary data to encode in the Data Matrix (supports up to 2,335 alphanumeric or 3,116 numeric characters)
- `size` (string, optional) - Matrix dimensions: auto-sized based on content, or manually specified (e.g., "10x10", "12x12")
- Example: content="SERIAL:12345678" or content="https://example.com/product/ABC123"

## Notes

- Include a quiet zone (white border) of at least 1 module width around the code for reliable scanning
- Use high contrast black on white for maximum readability
- L-shaped finder pattern (solid black on left and bottom edges) is mandatory for orientation
- Alternating (clock) pattern on top and right edges provides timing reference
- ECC 200 error correction is the modern standard (supports up to 30% data recovery)
- Recommended libraries: `pylibdmtx` or `treepoem` (Python), or `bwip-js` (JavaScript)
- Output should be scalable; vector format or high-resolution PNG (300+ DPI) recommended for printing

## What a good version looks like

- A good version shows: the L-shaped finder pattern as two solid black edges, on the left and along the bottom, as the Notes ask, unbroken and meeting in the lower left corner.
- A good version shows: the clock pattern of alternating black and white modules along the top and right edges, as the Notes ask, in step with the rows and columns of the grid.
- A good version shows: square modules of one size on a regular grid, black on white as the Notes ask, with sharp edges and no gradient or transparency; module positions follow from the symbology, not from data axes.
- A good version shows: a quiet zone of blank white around all sides of the symbol, as the Notes ask, free of text and other marks.
- A good version shows: the basic variant's single symbol: besides the finder pattern, the clock pattern, the data modules and the quiet zone, no logo or picture inside the code, tinted or highlighted modules or regions, reference lines, callouts on the code, or second symbol.
- Expected, not a defect: no data axes, ticks, grid or legend, a data region that looks like random noise, a sparse black and white picture, and a white tile behind the symbol in the dark theme.
