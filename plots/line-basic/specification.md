# line-basic: Basic Line Plot

## Description

A basic line plot connects data points with straight lines to show how a continuous variable changes over a sequence or time. It's ideal for revealing trends, patterns, and changes in data over ordered intervals. The simplicity of a single-line design makes it easy to interpret at a glance.

## Applications

- Tracking stock prices or financial metrics over trading days
- Monitoring website traffic or user engagement over time
- Visualizing temperature changes throughout a day or season

## Data

- `x` (numeric/datetime) - Sequential or time values representing the independent variable
- `y` (numeric) - Continuous values representing the measured quantity
- Size: 10-200 points (enough to show trends without clutter)
- Example: Daily temperature readings, monthly sales figures

## Notes

- Clean, minimal design with a single line
- Clear axis labels for both X and Y axes
- Grid lines for improved readability
- Markers on data points are optional but can enhance visibility

## What a good version looks like

- One continuous line connects the values in x order; with a single series no legend is needed, because the axis label names the quantity.
- Real series wiggle: short-term noise, dips and plateaus are expected, not a defect, and a perfectly smooth curve suggests fabricated data unless the scenario is a model output.
- Markers are optional; when drawn they stay small enough that the line still reads as a line, and the line is never smoothed past the points it connects.
- Missing values, if the data has any, show as a gap in the line rather than a straight bridge across it.
- The y axis spans the data: it includes zero only when the data sits near it or the quantity is a count from zero, and is never forced to zero when that would flatten the signal; the basic variant stays one line — no second series, trend line, shaded band or event annotations.
