# errorbar-basic: Basic Error Bar Plot

## Description

An error bar plot displays data points with associated uncertainty or variability represented by bars extending above and below (or left and right of) each point. Error bars commonly represent standard deviation, standard error, confidence intervals, or min/max ranges. This visualization is essential for communicating the reliability and precision of measurements or statistical estimates.

## Applications

- Scientific research presenting experimental results with measurement uncertainty
- Statistical analysis comparing group means with confidence intervals
- Quality control monitoring showing acceptable tolerance ranges around targets
- Clinical trials displaying treatment effects with error margins

## Data

- `x` (categorical or numeric) - Categories or positions on the x-axis
- `y` (numeric) - Central values representing mean, median, or measured values
- `error` (numeric) - Error magnitude for symmetric error bars, or tuple/pair for asymmetric errors
- Size: 3-20 groups/points for clarity

## Notes

- Error bars should have visible caps (horizontal lines at ends) to clearly mark the error range
- Use consistent error bar widths across all data points
- Consider using different colors to distinguish between groups when comparing multiple series
- Asymmetric error bars may be needed for skewed distributions or log-transformed data

## What a good version looks like

- A good version shows: one marker per group or position at its central value, with an error bar drawn through it from the lower to the upper bound, on a value axis that spans every error bar in full, and no marker moved off its value.
- A good version shows: visible caps at both ends of every error bar, with one cap width and one line weight across all data points, as the Notes ask, visible against the page in both themes.
- A good version shows: a distinct marker at every central value, drawn on top of its error bar, so each reads as a point with whiskers rather than a bare line or a box.
- A good version shows: the basic variant's points and error bars only, in one color, or one color per group as the Notes allow when several series are compared, and no bars beneath the points, trend or reference lines, tolerance or highlight bands, highlighted points, or callouts.
- Expected, not a defect: error bars of very different length, intervals of neighboring points that overlap, unequal arms where the errors are asymmetric, as the Notes allow, and a value axis that does not start at zero.
