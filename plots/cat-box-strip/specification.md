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

## What a good version looks like

- A good version shows: for each category a box from the first to the third quartile with a median line and whiskers, and that category's observations drawn as individual points over the box, as the Notes ask.
- A good version shows: every point at its value on the value axis and spread only across the category direction by jitter, inside its own category's band rather than drifting into a neighbor's.
- A good version shows: translucent points, as the Notes ask, small or faint enough that the box, its median line and its whiskers stay readable through and between them in both themes.
- A good version shows: one shared value axis for all categories that is not forced to zero, so boxes and point clouds compare directly.
- Expected, not a defect: sideways jitter offsets, which are layout rather than data, points that still overlap where a category is dense, points beyond the whiskers, categories with visibly different numbers of points, and skewed or lumpy point clouds.
