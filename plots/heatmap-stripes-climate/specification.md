# heatmap-stripes-climate: Climate Warming Stripes

## Description

Climate warming stripes (also known as "warming stripes") display temperature anomaly data as a sequence of vertical colored bars, one per year, using a blue-to-red diverging colormap. Created by climate scientist Ed Hawkins, this minimalist visualization strips away axes, labels, and gridlines to communicate long-term warming trends through pure color encoding. The progression from cool blues to warm reds makes temperature change immediately visible at a glance.

## Applications

- Communicating climate change trends to general audiences and non-scientists
- Showing long-term temperature anomalies for any geographic location or global averages
- Environmental reporting, science communication, and media graphics
- Educational materials illustrating global warming over the instrumental record

## Data

- `year` (integer) - calendar year of observation (e.g., 1850-2024)
- `anomaly` (numeric) - temperature anomaly in degrees Celsius relative to a baseline period
- Size: 100-175 rows (one per year)
- Example: Global mean temperature anomalies relative to 1961-1990 baseline from HadCRUT or NASA GISS datasets

## Notes

- No axes, no labels, no tick marks, no gridlines — this is a pure data visualization
- Use a blue-to-red diverging colormap centered at 0 (e.g., blues like #08306b for cold anomalies, reds like #67000d for warm anomalies)
- Each bar should fill equal width with no gaps between bars
- Target aspect ratio approximately 3:1 (wide and short) to emphasize the horizontal time progression
- Color scale should be symmetric around zero so that equal positive and negative anomalies have equal visual intensity
