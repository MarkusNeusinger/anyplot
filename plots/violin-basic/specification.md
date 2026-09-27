# violin-basic: Basic Violin Plot

## Description

A violin plot combining a box plot with a kernel density estimation on each side, showing the distribution shape of numerical data. The width of the violin at each point represents the frequency of data values at that level. Excellent for comparing distributions across categories while revealing their underlying shape, providing more detail than a traditional box plot.

## Applications

- Comparing salary distributions across job titles
- Analyzing test score distributions by school
- Comparing customer spending patterns by segment
- Research: comparing measurement distributions between groups

## Data

- `category` (string) - group labels for comparison
- `value` (numeric) - numerical values to plot
- Size: 30-1000 points per category, 2-6 categories
- Example: Test scores (50-100) across 4 class groups with distinct distribution shapes

## Notes

- Show quartile markers inside the violin
- Use mirrored density on both sides
- Include median line

## What a good version looks like

- Each category gets a mirrored density shape; widths, heights and areas differ between categories, and multimodal or skewed shapes are the point of the chart, not an imbalance to fix.
- Quartile markers and a median line sit inside every violin and stay visible against the violin fill in both themes.
- All violins share one value axis that is not forced to zero, so their positions compare directly, and each violin's tails end near its data range instead of trailing far beyond it.
- One colour for all violins, or one colour per category, is correct; the basic variant adds no overlaid points, swarm, split halves or annotations.
