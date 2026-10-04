# heatmap-calendar: Basic Calendar Heatmap

## Description

A calendar heatmap visualizes time-series data on a calendar grid, where each day is represented as a cell and color intensity indicates the value magnitude. The layout follows a calendar structure with days as cells, weekdays as rows, weeks as columns, and months as labeled sections along the top. This visualization excels at revealing daily patterns, seasonal trends, and temporal anomalies over extended time periods.

## Applications

- GitHub-style contribution graphs showing daily coding activity
- Daily sales or website traffic patterns across months
- Habit tracking visualization for personal productivity
- Weather data patterns showing temperature or precipitation by day

## Data

- `date` (datetime) - daily dates covering the time range
- `value` (numeric) - measurement or count for each day
- Size: 365-730 days (1-2 years) for optimal readability
- Example: daily commit counts, step counts, or temperature readings

## Notes

- Display weekday labels (Mon-Sun) on the y-axis
- Show month labels along the top or as section headers
- Use a sequential colormap (light to dark) for positive values
- Handle missing dates gracefully with neutral or empty cells
- Include a color scale legend for value interpretation

## What a good version looks like

- A good version shows: each day as an equal-sized cell at its own date in a calendar grid, with the weekday labels (Mon-Sun) the Notes ask for on the y axis, so a cell's weekday and week read from its position.
- A good version shows: month labels along the top or as section headers, as the Notes ask, lined up with where each month's days begin; where the data spans more than a year, each year is set apart or labeled.
- A good version shows: a sequential colormap running from light to dark for positive values, as the Notes ask, and a color scale legend from which a cell's color can be read back as a value.
- A good version shows: days without data as neutral or empty cells, as the Notes ask, distinguishable in both themes from days with a low value.
- Expected, not a defect: partial first and last weeks that leave the ends of the grid ragged, months that begin in mid-week so month boundaries are stepped, many pale days with a few dark ones, and a weekly rhythm that shows as stripes.
