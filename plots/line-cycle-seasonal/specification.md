# line-cycle-seasonal: Cycle Plot (Seasonal Subseries)

## Description

A cycle plot, also known as a seasonal subseries plot (introduced by William Cleveland), separates the seasonal pattern of a time series from the trend within each season. The series is split by seasonal period (e.g. one group per month or weekday); within each group the values are drawn in chronological order as a small line, and a horizontal reference line marks that group's mean. Comparing the mean lines across groups reveals the seasonal effect, while the slope of each subseries reveals the trend within that season — two patterns that are entangled in a standard time series plot.

## Applications

- Analyzing monthly retail sales to see which months are seasonally strongest (mean differences) and whether each month is growing or shrinking year over year (within-group slope)
- Examining electricity demand by hour-of-day or day-of-week to isolate recurring usage cycles from long-term growth
- Studying climate records (e.g. average temperature by month across many years) to distinguish the annual cycle from warming trends within individual months

## Data

- `season` (categorical/ordinal) - The seasonal group each observation belongs to (e.g. month name Jan–Dec, weekday Mon–Sun, or hour 0–23); defines the panels/groups along the x-axis
- `cycle` (ordinal/datetime) - The position within the series that orders points inside each group chronologically (e.g. year, or sequential cycle index)
- `value` (numeric) - The measured quantity plotted on the y-axis
- Size: 4-12 seasonal groups, each with ~5-30 chronological observations (roughly 30-300 points total; minimum several full cycles)
- Example: Monthly airline passengers grouped by month across ~12 years; average monthly temperature over 30 years

## Notes

- Lay seasonal groups left to right along the x-axis (Jan, Feb, ... or Mon, Tue, ...); within each group plot the chronological subseries as a thin connected line
- Draw a horizontal reference line at each group's mean spanning the width of that group — these mean lines are the key visual for comparing seasons
- Keep a shared y-axis across all groups so heights are directly comparable; separate groups with subtle gaps or light vertical dividers
- Order seasonal groups by their natural calendar/clock order, not by value
- Optionally draw all group-mean lines at a consistent style/color to emphasize the seasonal-mean comparison versus the within-group trend lines
- A single shared panel with grouped subseries is preferred over fully separate faceted subplots, so mean levels can be compared across the whole figure
