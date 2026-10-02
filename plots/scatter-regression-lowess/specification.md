# scatter-regression-lowess: Scatter Plot with LOWESS Regression

## Description

A scatter plot with a LOWESS (Locally Weighted Scatterplot Smoothing) regression curve overlaid. LOWESS is a non-parametric method that fits smooth curves by performing local weighted regressions at each point, adapting to local data patterns without assuming a specific functional form. This makes it ideal for exploring complex relationships where the underlying pattern is unknown or varies across the data range.

## Applications

- Exploring non-linear relationships in exploratory data analysis where the true relationship is unknown
- Visualizing trends in economic data where patterns may change over different value ranges
- Analyzing biological dose-response curves that don't follow standard mathematical models

## Data

- `x` (numeric) - Independent variable values plotted on the horizontal axis
- `y` (numeric) - Dependent variable values plotted on the vertical axis
- Size: 50-500 points recommended (LOWESS benefits from moderate sample sizes)
- Example: Data with a complex, non-linear relationship that varies across the x-axis range

## Notes

- LOWESS curve should be visually distinct from scatter points (solid line, contrasting color)
- Use moderate smoothing bandwidth (frac ~0.3-0.5) as default for balanced smoothness
- Points should have moderate transparency (alpha ~0.5-0.7) to show density and the fitted curve clearly
- Include axis labels and descriptive title mentioning LOWESS smoothing
- Optional: Show confidence band around the LOWESS curve if library supports it
- The curve should appear smooth without excessive oscillation or overfitting to noise

## What a good version looks like

- A good version shows: every observation as a translucent point at its exact (x, y) value, as the Notes ask, with one solid LOWESS curve on top in a color that contrasts with the points.
- A good version shows: a curve that follows the local center of the cloud through its bends, smooth as the Notes ask: it neither wiggles from point to point nor flattens into a near-straight line that ignores visible curvature.
- A good version shows: a curve that spans the data's x range and ends at the outermost points, with nothing extrapolated beyond them.
- A good version shows: a title that mentions LOWESS smoothing, as the Notes ask, and the confidence band, if drawn as the Notes allow, semi-transparent around the curve with the points inside it still visible.
- Expected, not a defect: a curve with neither equation nor R² beside it, because LOWESS has no single formula, a slope that changes or reverses along x, wider scatter in some x ranges than in others, and outliers the curve does not chase.
