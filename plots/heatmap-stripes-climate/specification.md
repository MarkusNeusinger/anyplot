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
- Stripes fill a band clearly wider than it is tall (about 3:1 where the canvas allows; a 16:9 canvas filled edge to edge is fine) to emphasize the horizontal time progression
- Color scale should be symmetric around zero so that equal positive and negative anomalies have equal visual intensity

## What a good version looks like

- A good version shows: a vertical stripe for every year, in chronological order from left to right, each colored by that year's anomaly, all of equal width and touching, with no gaps between them, as the Notes ask.
- A good version shows: a blue-to-red diverging colormap centered on zero with limits symmetric around it, as the Notes ask, so cold and warm anomalies of equal size get equal intensity and years near zero are the palest.
- A good version shows: the stripes alone as the plot, with no axes, labels, tick marks or gridlines, as the Notes ask, and each stripe running the full height of a band that is wider than it is tall.
- A good version shows: year-to-year variation within the long-term trend, warm and cool years interleaved instead of a smooth gradient, so the stripes read as observed data.
- Expected, not a defect: no axes, no legend and no color bar, so no value can be read off the plot, and far more of one end of the symmetric scale in use than the other, with the deepest blue or red going unused.
