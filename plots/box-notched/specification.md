# box-notched: Notched Box Plot

## Description

A notched box plot extends the standard box plot by adding notches around the median that represent a confidence interval. If the notches of two boxes do not overlap, this provides visual evidence that the medians differ significantly. This variant is particularly valuable for quick visual hypothesis testing and comparing group medians in statistical analysis.

## Applications

- Comparing treatment effects across experimental groups in research studies
- Analyzing salary distributions across departments with statistical significance testing
- Quality control: identifying statistically different production batches
- Clinical trials: comparing patient outcomes between control and treatment groups

## Data

- `category` (string) - group labels for comparison
- `value` (numeric) - numerical values to plot
- Size: 20-500 points per category, 2-8 categories
- Note: Notch reliability improves with larger sample sizes (n > 20 recommended)

## Notes

- Display notches at 95% confidence interval around the median
- Include standard box plot elements (median, quartiles, whiskers at 1.5*IQR)
- Show outliers as individual points beyond the whiskers
- Use different colors for each category to aid comparison
- Notch depth calculated as ±1.57 × IQR / √n

## What a good version looks like

- A good version shows: every box pinched inward on both sides around its median, the notch spanning the confidence interval around the median that the Notes define, with the median line at the narrowest point.
- A good version shows: notches distinct enough from the rest of the box outline, in both themes, that a viewer can judge whether the notches of two boxes share any range on the value axis.
- A good version shows: the standard box elements the Notes ask for: a box from the first to the third quartile, whiskers reaching to the most extreme values within 1.5 times the IQR, and outliers as individual points beyond the whiskers at their values.
- A good version shows: a different color for each category, as the Notes ask, on one shared value axis that is not forced to zero.
- Expected, not a defect: notches of very different length, longer for a small or widely spread group, including a notch that reaches past a quartile and folds the box corner outward, notches of neighboring boxes that overlap, and outlier points beyond the whiskers.
