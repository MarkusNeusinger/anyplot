# line-timeseries: Time Series Line Plot

## Description

A time series line plot displays data points connected by lines over a datetime x-axis, with smart date formatting that automatically adjusts tick labels based on the time scale (days, months, years). This plot type is essential for temporal data analysis where proper date formatting and readability are critical. Unlike basic line plots, time series plots handle datetime parsing, timezone awareness, and intelligent tick label formatting.

## Applications

- Tracking stock prices or financial instrument performance over trading periods
- Monitoring sensor readings (temperature, humidity, pressure) over time
- Analyzing website traffic, user engagement, or API usage patterns over days/months

## Data

- `date` (datetime) - Timestamp values representing points in time
- `value` (numeric) - Continuous measurements or observations at each timestamp
- Size: 30-500 points (enough to show meaningful temporal patterns)
- Example: Daily closing prices for a stock over one year, hourly temperature readings for a week

## Notes

- Use intelligent date formatting that adapts to the time range (e.g., "%H:%M" for hours, "%b %d" for days, "%Y" for years)
- Rotate or stagger tick labels if needed to prevent overlap
- Include grid lines on both axes for improved readability
- Consider using date locators (e.g., MonthLocator, DayLocator) for consistent tick spacing
- The x-axis should clearly communicate the temporal nature of the data

## What a good version looks like

- A good version shows: one line joining the observations in time order on a true date axis, each point at its own timestamp, so uneven spacing in time shows as uneven spacing along the axis.
- A good version shows: date tick labels in a format that fits the time span of the data (times of day for hours, days and months for weeks, years for long ranges), at regular calendar intervals, rotated or staggered only where they would otherwise collide.
- A good version shows: grid lines on both axes, as the Notes ask, kept subordinate to the data line and visible in both themes.
- A good version shows: missing values, if the data marks any explicitly, as breaks in the line rather than a straight bridge across them; observations that are merely unevenly spaced stay connected.
- A good version shows: a y axis that spans the data and is never forced to zero when that would flatten the signal.
- Expected, not a defect: seasonality, spikes, short-term noise and level shifts, a line that looks dense where many observations share little width, and no legend for a single series, because the axis label names the quantity.
