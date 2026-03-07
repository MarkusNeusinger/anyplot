# pictogram-basic: Pictogram Chart (Isotype Visualization)

## Description

A pictogram chart represents quantities using repeated icons or symbols, where each icon stands for a fixed number of units. Inspired by Otto Neurath's ISOTYPE system, this visualization makes numerical comparisons more intuitive and engaging than plain bar charts. It is especially effective for public-facing data communication and infographics where visual appeal and immediate comprehension are important.

## Applications

- Comparing population counts across countries using person icons, where each icon represents 1 million people
- Showing annual production volumes of different crops using crop-specific symbols in an agricultural report
- Visualizing survey results (e.g., customer satisfaction ratings) with star or smiley icons for a marketing dashboard

## Data

- `category` (string) - The group or item being compared (e.g., country, product, department)
- `value` (numeric) - The quantity each category represents
- `icon` (string, optional) - Symbol or marker to use per category (defaults to a single icon type)
- Size: 3-8 categories for best readability
- Example: Fruit production dataset with categories (Apples, Oranges, Bananas) and values (35, 22, 18) where each icon represents 5 units

## Notes

- Each icon should represent a consistent unit value (e.g., 1 icon = 10 units); display a legend indicating this
- Partial icons (e.g., half-filled) should represent fractional remainders
- Icons should be arranged in a grid-like row for each category, aligned left for easy comparison
- Use simple, recognizable shapes (circles, squares, or Unicode symbols) as icons since most plotting libraries lack built-in pictogram support
- Category labels should appear on the left axis, similar to a horizontal bar chart layout
