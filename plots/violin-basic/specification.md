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

- A good version shows: a mirrored density shape for each category.
- Expected, not a defect: widths and heights that differ between categories (depending on whether violins are scaled by area, count or width), and multimodal or skewed shapes; they are the point of the chart, not an imbalance to fix.
- A good version shows: quartile markers and a median line inside every violin, visible against the violin fill in both themes.
- A good version shows: one shared value axis for all violins that is not forced to zero, so their positions compare directly, with each violin's tails ending near its data range instead of trailing far beyond it.
- A good version shows: the basic variant's colors only: one color for all violins or one per category, and no overlaid points, swarm, split halves, highlighted violins, reference lines across the plot, or callouts and other annotations.
