# barcode-code128: Code 128 Barcode

## Description

A Code 128 barcode visualization that encodes alphanumeric data into a high-density linear barcode pattern. Code 128 is a widely-used 1D barcode format that supports the full 128 ASCII character set, with three code subsets (A, B, C) that can be switched dynamically for optimal encoding efficiency. This visualization generates scannable barcodes commonly found on shipping labels, industrial parts, and healthcare specimens.

## Applications

- Generating shipping labels and package tracking codes for logistics operations
- Creating asset identification tags for inventory and equipment management
- Producing specimen and sample labels for healthcare and laboratory workflows
- Labeling industrial parts and components for manufacturing traceability
- Generating membership cards and badge barcodes for access control systems

## Data

- `content` (string) - The alphanumeric text to encode in the barcode
- `subset` (string, optional) - Preferred code subset: A (control + uppercase), B (ASCII printable), C (numeric pairs), or Auto
- Size: Up to 48 characters recommended for standard label width; supports full ASCII range
- Example: "SHIP-2024-ABC123" or "https://pyplots.ai"

## Notes

- Include quiet zones (white space) on left and right sides for reliable scanning
- Start pattern indicates the code subset (A, B, or C)
- Check digit is mandatory and calculated using modulo 103 algorithm
- Stop pattern is required at the end of every Code 128 barcode
- Human-readable text should appear below the barcode for visual verification
- Use high contrast black bars on white background for maximum scan reliability
- Recommended bar width ratio maintains standard Code 128 proportions
- Libraries: `python-barcode`, `reportlab`, or manual rendering with PIL/matplotlib

## What a good version looks like

- A good version shows: one row of parallel vertical bars of equal height in the standard order: a start pattern, the data characters, the check character the Notes require and the stop pattern closing the symbol on the right.
- A good version shows: bar and space widths that follow from the encoding of the content, each a whole number of modules in the standard Code 128 proportions the Notes ask for; position is construction here, so widths are never drawn at random or evened out.
- A good version shows: quiet zones as blank space to the left and right of the bars, as the Notes ask, kept free of text and other marks.
- A good version shows: the human-readable text below the bars, as the Notes ask, reading the encoded content and standing clear of the bars.
- A good version shows: solid, sharp-edged black bars on a white ground, as the Notes ask, with no gradient or transparency; labels naming the start, data, check and stop parts, if drawn, sit outside the bars and line up with the parts they name.
- Expected, not a defect: no data axes, ticks, grid or legend, a sparse monochrome picture, an irregular rhythm of thick and thin bars, a single code subset in use, and a white tile behind the symbol in the dark theme.
