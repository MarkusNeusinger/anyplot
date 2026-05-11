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
