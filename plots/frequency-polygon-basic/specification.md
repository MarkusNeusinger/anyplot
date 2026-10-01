# frequency-polygon-basic: Frequency Polygon for Distribution Comparison

## Description

A frequency polygon connects the midpoints of histogram bins with straight line segments, creating a smooth outline of the distribution shape. This visualization excels at comparing multiple distributions simultaneously since lines overlap without obscuring each other, unlike stacked or overlapping histogram bars. Frequency polygons reveal differences in central tendency, spread, skewness, and modality across groups with minimal visual clutter.

## Applications

- Comparing test score distributions across multiple classes or exam sessions
- Analyzing response time distributions between experimental conditions in psychology research
- Visualizing age distributions across different customer segments or cohorts

## Data

- `values` (numeric) - The continuous variable to bin and display
- `group` (categorical) - The grouping variable distinguishing each distribution
- Size: 50-1000 observations per group recommended; works well with 2-5 groups
- Example: Heights by age group, salaries by department, reaction times by treatment

## Notes

- Use distinct line colors and/or styles (solid, dashed) to differentiate groups
- Include a legend clearly identifying each group
- Consider adding markers at data points for small datasets
- Extend lines to zero at both ends to close the polygon shape
- Align bin edges across all groups for accurate comparison
- Semi-transparent fill beneath lines can enhance visual appeal while preserving clarity

## What a good version looks like

- A good version shows: for each group, straight line segments joining one point per bin, placed at the bin's midpoint and at the group's frequency in that bin, with no smoothing between the points.
- A good version shows: every line extended to zero at both ends, as the Notes ask, so each polygon closes on the baseline of a frequency axis that starts at zero.
- A good version shows: bin edges aligned across all groups, as the Notes ask, so the vertices of every group sit at the same x positions.
- A good version shows: groups told apart by line color, line style or both, and named in a legend, as the Notes ask, with every line traceable in both themes where the lines cross.
- A good version shows: the basic variant's one polygon per group, with the markers and the semi-transparent fill the Notes allow, and no histogram bars beneath, smoothed density curves, mean or other reference lines, highlighted segments or bands, or callouts.
- Expected, not a defect: angular lines with sharp peaks, lines that cross each other, polygons of different height and spread, and jagged stretches where neighboring bins differ.
