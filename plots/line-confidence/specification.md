# line-confidence: Line Plot with Confidence Interval

## Description

A line plot with a confidence interval displays a central trend line (typically mean or median) surrounded by a shaded band representing uncertainty or variability. The combination of a clear central line and semi-transparent confidence region effectively communicates both the estimated value and its associated uncertainty, making it essential for visualizing statistical estimates, model predictions, and forecast ranges.

## Applications

- Displaying model predictions with uncertainty bounds in machine learning
- Showing statistical estimates with confidence intervals in research
- Visualizing time series forecasts with prediction intervals
- Presenting regression results with standard error bands

## Data

- `x` (numeric/datetime) - Independent variable, often representing time or sequence
- `y` (numeric) - Central values representing mean, median, or predicted values
- `y_lower` (numeric) - Lower bound of the confidence interval
- `y_upper` (numeric) - Upper bound of the confidence interval
- Size: 20-200 data points
- Example: Time series with 95% confidence interval, regression predictions with standard error

## Notes

- Use a solid, prominent line for the central trend
- Shaded band should be semi-transparent (alpha 0.2-0.4) to show overlap and maintain readability
- Include a legend that clearly identifies both the central line and confidence band
- Consider using contrasting but related colors (e.g., dark blue line with light blue band)
- Grid lines improve readability of the underlying values

## What a good version looks like

- A good version shows: a solid, prominent central line joining the central values in x order, as the Notes ask, drawn on top of the band and the strongest mark in the plot.
- A good version shows: a shaded band that spans from the lower to the upper bound at every x and encloses the central line, with nothing filled outside the bounds.
- A good version shows: a semi-transparent band, as the Notes ask, so gridlines and any overlapping band stay visible through it in both themes, while the band stays distinct from the page.
- A good version shows: a legend that identifies both the central line and the confidence band, as the Notes ask, and says what the band represents, such as a confidence or a prediction interval.
- A good version shows: a band that visibly belongs to its line, in a lighter tone of the line's color if the related colors the Notes suggest are used, and in any case not mistakable for a second series.
- Expected, not a defect: a band whose width changes along x, including one that widens toward the end of a forecast, a band that is not symmetric about the line, and a central line with short-term noise.
