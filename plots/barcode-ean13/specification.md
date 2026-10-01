# barcode-ean13: EAN-13 Barcode

## Description

A standard EAN-13 barcode visualization commonly used for retail products worldwide. The plot renders a scannable linear barcode encoding a 13-digit number with proper bar widths, guard patterns, and human-readable digits. This visualization is essential for product identification, inventory management, and point-of-sale systems.

## Applications

- Product labeling for retail and e-commerce inventory management
- Supply chain tracking and logistics identification
- Educational demonstrations of barcode encoding technology
- Generating scannable labels for custom product catalogs

## Data

- `code` (string) - 12 or 13 digit numeric string; check digit auto-calculated if 12 digits provided
- Structure: First 2-3 digits = country code, next 4-5 digits = manufacturer code, next 5 digits = product code, final digit = check digit
- Size: Exactly 12 or 13 numeric characters
- Example: "5901234123457" (Polish product) or "4006381333931" (German product)

## Notes

- Include quiet zones (white space) of at least 9 module widths on left and 9 on right
- Render start guard (101), center guard (01010), and end guard (101) patterns
- Use standard bar width ratios: bars are 1, 2, 3, or 4 modules wide
- Display human-readable digits below the barcode with the first digit outside left guard
- Recommended output size: at least 200 pixels wide for reliable scanning
- Libraries: `python-barcode`, `treepoem`, or manual rendering with matplotlib
- Print resolution should be 300 DPI minimum for physical labels

## What a good version looks like

- A good version shows: the symbol's standard structure from left to right: a start guard, the left group of digit patterns, a center guard, the right group of digit patterns and an end guard, with the three guard patterns the Notes ask for recognizable as thin paired bars.
- A good version shows: bar and space widths that follow from the encoded digits, each a whole number of modules, as the Notes ask; position is construction here, so widths are never drawn at random or evened out.
- A good version shows: the human-readable digits below the bars, as the Notes ask, matching the encoded number, with the first digit outside the left guard and the other digits under the two halves of the symbol.
- A good version shows: guard bars that stand out from the digit bars, by convention drawn longer so that they reach down between the groups of digits.
- A good version shows: quiet zones as blank space to the left and right of the bars, as the Notes ask, with solid, sharp-edged bars in strong contrast with the spaces in both themes.
- Expected, not a defect: no data axes, ticks, grid or legend, a sparse monochrome picture, an irregular rhythm of thick and thin bars, and a light tile behind the symbol in the dark theme.
