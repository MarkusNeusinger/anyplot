# point-basic: Point Estimate Plot

## Description

A point estimate plot displays central tendency values (means, medians, or other estimates) with confidence intervals or error bars for each category. Each point represents the estimate, and the lines extending from it show the uncertainty range.

## Applications

- Comparing group means with statistical uncertainty
- Displaying regression coefficients with confidence intervals
- Treatment effect visualization in clinical trials
- Survey results with margin of error
- Meta-analysis effect size summaries

## Data

- `category` (categorical) - The group or category identifier
- `estimate` (numeric) - The point estimate value (mean, median, coefficient, etc.)
- `lower_bound` (numeric) - Lower confidence limit
- `upper_bound` (numeric) - Upper confidence limit
- Size: 3–100 categories recommended for clarity

Example:
```
Category | Estimate | Lower | Upper
---------|----------|-------|------
Group A  | 5.2      | 4.1   | 6.3
Group B  | 3.8      | 2.9   | 4.7
Group C  | 6.1      | 5.5   | 6.7
```

## Notes

- Horizontal orientation is common for reading category labels
- Points should be clearly visible (distinct markers)
- Confidence intervals typically at 95% level
- Consider adding a reference line (e.g., at zero or null hypothesis)
- Error bars should have caps at endpoints

## What a good version looks like

- A good version shows: one marker per category at its estimate, with an interval line through it from the lower to the upper bound, on a shared value axis that spans every interval in full, and no marker moved off its estimate.
- A good version shows: distinct markers that stay clearly visible on top of their interval lines, as the Notes ask, in both themes.
- A good version shows: caps at both ends of every interval, as the Notes ask, visible against the page in both themes.
- A good version shows: every category named at its own row or position, in the horizontal layout the Notes call common or a vertical one, and in a meaningful order: by estimate, or the categories' natural order when they have one.
- A good version shows: the basic variant's one estimate and interval per category, besides the single reference line the Notes allow, such as one at zero or the null value, and no second series, bars beneath the points, trend lines, highlighted rows or bands, or callouts.
- Expected, not a defect: intervals of very different width, intervals of neighboring categories that overlap, an estimate that sits off-center in its interval, intervals that cross the reference line, and a value axis that does not start at zero.
