# box-basic: Basic Box Plot

## Description

A box plot (box-and-whisker plot) showing the distribution of numerical data through quartiles. Displays the median, first and third quartiles as a box, with whiskers extending to show the data range. Essential for comparing distributions across categories and identifying outliers.

## Applications

- Comparing salary distributions across departments
- Analyzing test score distributions by class
- Quality control: comparing measurements across production batches
- Research: comparing experimental groups

## Data

- `category` (string) - group labels for comparison
- `value` (numeric) - numerical values to plot
- Size: 20-500 points per category, 2-8 categories
- Example: Test scores across 5 classes with 50-100 students each

## Notes

- Show median line within the box
- Display outliers as individual points
- Include whiskers at 1.5*IQR
- Use different colors for each category

## What a good version looks like

- A good version shows: one box per category spanning the first to the third quartile, with a median line inside it, as the Notes ask, that stands out against the box fill in both themes.
- A good version shows: whiskers reaching to the most extreme values within 1.5 times the IQR of the box, and every value beyond them drawn as an individual point at its value, as the Notes ask.
- A good version shows: one shared value axis for all boxes that is not forced to zero, so medians and spreads compare directly.
- A good version shows: the basic variant's one box per category, each in a different color as the Notes ask, and, besides the median line, whiskers and outlier points, no overlaid strip or swarm points, mean markers, notches, density shapes, reference or mean lines, highlighted boxes or bands, or callouts.
- Expected, not a defect: outlier points beyond the whiskers, categories with none at all, boxes of very different length, a median that sits off-center in its box and whiskers of unequal length; they are the point of the chart, not an imbalance to fix.
