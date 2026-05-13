# cat-box-strip: Box Plot with Strip Overlay

## Description

A combined visualization that overlays individual data points (strip plot) on top of a box plot. This provides both summary statistics (median, quartiles, whiskers) and visibility of the actual data distribution.

## Applications

- Complete distribution visualization
- Identifying outliers with context
- Comparing groups with sample size awareness
- Statistical presentations requiring raw data visibility

## Data

- `category` (categorical) - Groups or categories to compare
- `value` (numeric) - Numeric values to analyze
- Size: 50-500+ points (larger samples better reveal distribution shape)
- Example:
```
Category | Value
---------|-------
A        | 45.2
A        | 52.1
B        | 38.7
B        | 41.3
```

## Notes

- Strip points overlay the box plot
- Box shows median, Q1, Q3; whiskers show range
- Points use jitter and transparency to reduce overlap
- Reveals sample size and distribution shape together
