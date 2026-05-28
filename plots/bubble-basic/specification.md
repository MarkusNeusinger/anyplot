# bubble-basic: Basic Bubble Chart

## Description

A bubble chart extending scatter plots by adding a third dimension through bubble size. Each point's position shows two variables (x, y) while the bubble size represents a third quantitative variable. This visualization is excellent for understanding relationships between three numerical variables simultaneously, revealing patterns that would be hidden in traditional 2D scatter plots.

## Applications

- Market analysis: comparing companies by revenue vs growth rate with bubble size showing market share
- City comparison: population vs GDP per capita with bubble size representing total area
- Product portfolio analysis: price vs quality rating with bubble size indicating sales volume
- Scientific research: visualizing three continuous measurements across samples

## Data

- `x` (numeric) - Horizontal position variable
- `y` (numeric) - Vertical position variable
- `size` (numeric) - Bubble size variable (third dimension)
- Size: 50-500 data points recommended for clear visualization
- Size range: 10–100 recommended for the bubble size column values
- Example: Company financial metrics (revenue vs. growth rate with market share as bubble size)

## Notes

- Scale bubble sizes by area (not radius) for accurate visual perception
- Use transparency (alpha ~0.5-0.7) to handle overlapping bubbles
- Include a size legend to explain bubble scaling
- Color can optionally distinguish categories but is not required for the basic variant
- Ensure minimum bubble size is visible and maximum doesn't overwhelm the chart
