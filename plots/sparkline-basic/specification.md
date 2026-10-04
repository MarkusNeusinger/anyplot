# sparkline-basic: Basic Sparkline

## Description

A sparkline is a small, condensed line chart designed to be embedded inline with text or in dashboard cells. It shows trends at a glance without axes, axis labels, or detailed scales - pure data visualization in minimal space. The defining characteristic is extreme minimalism: a single continuous line that conveys the shape of data without any chart chrome.

## Applications

- Dashboard KPI trend indicators showing metric changes over time
- Inline stock price trends embedded in financial tables or reports
- Table cells displaying metric history for quick comparison across rows
- Small multiples for comparing many series side-by-side

## Data

- `values` (numeric array) - Sequential values representing the trend to display
- Size: 10-100 data points (enough to show meaningful trends while staying compact)
- Example: Daily sales figures, hourly temperature readings, stock closing prices

## Notes

- No axes, axis labels, or gridlines - pure visualization
- Compact aspect ratio (wide and short, typically 4:1 to 8:1)
- Optional: highlight min/max points with colored dots
- Optional: highlight first/last points for reference
- Optional: fill under line for area effect
- Optional: the series name and its last value as text beside the line (Tufte's convention); no other labels
- Line should be thin and clean for clarity at small sizes

## What a good version looks like

- A good version shows: a single thin line joining the values in sequence, as the Notes ask, never smoothed past its points, in a plot area that is wide and short.
- A good version shows: each sparkline scaled to its own range, so the line uses the full height of its small frame from lowest to highest value and the shape of the trend reads at a glance, unless several sparklines deliberately share one scale.
- A good version shows: dots on the minimum and maximum and on the first and last points, if drawn as the Notes allow, sitting exactly on the line at those values and colored so they stand out from it.
- A good version shows: the basic variant's single line, with the min, max, first and last dots, the fill and the name and last value beside it that the Notes allow, and no axes, tick labels, gridlines, reference lines or normal-range bands, highlighted segments, trend line, second line, or callouts.
- Expected, not a defect: no axes, ticks, gridlines, frame or legend, and exact values that cannot be read off the line, apart from an optional last-value label; a sparkline shows the shape of the data, not its numbers.
