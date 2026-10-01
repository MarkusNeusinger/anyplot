# waffle-basic: Basic Waffle Chart

## Description

A waffle chart displays proportions using a grid of equal-sized squares where colored squares represent parts of a whole. Each square typically represents 1% of the total, making it easy to count and compare values visually. It provides an intuitive alternative to pie charts, offering more accurate perception of proportions.

## Applications

- Visualizing survey results and polling data to show response distributions
- Displaying budget allocation across spending categories
- Tracking progress towards goals (e.g., fundraising at 73% of target)
- Showing demographic breakdowns in population studies

## Data

- `category` (categorical) - Category labels for each segment
- `value` (numeric) - Proportions or percentages for each category
- Size: 2-6 categories typical
- Note: Values should sum to 100 or be normalized to percentages

## Notes

- Standard grid is 10x10 (100 squares) where each square = 1%
- Use distinct, contrasting colors for each category
- Include a legend identifying categories with their percentages
- Round values to whole squares for clean visualization

## What a good version looks like

- A good version shows: a grid of equal squares with even gaps, the Notes' standard 10x10 grid unless the scenario calls for another, in which every square stands for the same share of the whole; a square's position is layout, not data, so there are no axes or grid lines.
- A good version shows: each category as a count of whole squares equal to its rounded share, as the Notes ask, with no partly filled square and the categories together filling the grid.
- A good version shows: each category's squares together as one contiguous block, filled in one direction, row by row or column by column, so a share can be counted.
- A good version shows: one distinct, contrasting color per category and a legend that names each category with its percentage, as the Notes ask, with the squares visible against the page in both themes.
- A good version shows: the basic variant's single grid of squares: no second grid or small multiples, icons in place of squares, reference lines, highlighted squares or bands, or callouts beyond the legend.
- Expected, not a defect: blocks of very different size, including a category of only a square or two, a block that ends partway through a row or column, and shares rounded to whole squares that differ slightly from the exact values.
