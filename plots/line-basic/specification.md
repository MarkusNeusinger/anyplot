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

- A good version shows: one continuous line connecting the values in x order, never smoothed past the points it connects; markers, if drawn, stay small enough that the line still reads as a line.
- Expected, not a defect: short-term noise, dips and plateaus, and no legend for a single series, because the axis label names the quantity.
- A good version shows: a series that wiggles like real data; a perfectly smooth curve suggests fabricated data unless the scenario is a model output.
- A good version shows: missing values, if the data has any, as a gap in the line rather than a straight bridge across it.
- A good version shows: a y axis that spans the data: it includes zero only when the data sits near it or the quantity is a count from zero, and is never forced to zero when that would flatten the signal.
- A good version shows: the basic variant's single line: no second series, trend line, shaded band or event annotations.
