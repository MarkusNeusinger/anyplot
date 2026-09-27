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

## What a good version looks like

- A good version shows: each category as one left-aligned row of identical icons of one size and spacing, the icon count times one shared unit value giving the category's value, so row length compares like bar length.
- A good version shows: a legend stating the unit value of one icon, drawn with the same icon the rows use.
- A good version shows: a fractional remainder, where a value has one, as one partial icon at the row's end, cut or filled in proportion to the fraction, so it reads as part of an icon rather than a smaller whole one.
- A good version shows: the basic variant's icon rows only: one icon type and one color for every row, or one icon per category as the Data's optional icon column allows, with category labels on the left and no sub-group colors within a row or callouts.
- Expected, not a defect: no value axis, ticks or gridlines, because the icon count carries the value, and rows of very different lengths, including one that is only a partial icon.
