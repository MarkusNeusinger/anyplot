# scatter-connected-temporal: Connected Scatter Plot with Temporal Path

## Description

A scatter plot where data points are connected by lines in temporal order, revealing how two variables co-evolve over time. Unlike standard time series plots that show one variable against time, this plot encodes time as movement through 2D space, making cyclical patterns, regime changes, and directional trends visible. Popularized by the New York Times, it is a powerful tool for narrative data visualization.

## Applications

- Tracking the relationship between unemployment rate and inflation over decades (Phillips curve dynamics)
- Visualizing how a country's life expectancy and GDP per capita change together year-over-year
- Showing the co-evolution of temperature and CO2 concentration across climate epochs
- Analyzing how two financial indicators (e.g., price and volume) move together over trading sessions

## Data

- `x` (numeric) - First continuous variable plotted on the horizontal axis
- `y` (numeric) - Second continuous variable plotted on the vertical axis
- `time` (numeric or datetime) - Temporal ordering variable used to connect points sequentially
- `label` (string, optional) - Text labels for selected time points (e.g., year annotations)
- Size: 10-100 points (too many points create visual clutter)
- Example: Annual unemployment rate vs. inflation rate for a country over 30 years

## Notes

- Points should be connected in chronological order with line segments
- Key time points (e.g., start, end, notable years) should be annotated with text labels
- An arrow or color gradient along the path can indicate the direction of time
- Point markers should be visible at each data position to distinguish from a simple line plot
- Consider using a subtle color gradient (e.g., light to dark) to encode temporal progression
