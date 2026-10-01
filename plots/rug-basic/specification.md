# rug-basic: Basic Rug Plot

## Description

A rug plot displays individual data points as small tick marks along an axis, typically at the bottom or side of another plot. Unlike histograms or density plots that bin data, rug plots show the exact location of every observation. They reveal clustering patterns, gaps in data, and the precise distribution of values with minimal visual footprint.

## Applications

- Showing the underlying data points alongside a kernel density estimate or histogram
- Revealing gaps and clusters in continuous data that binning would hide
- Displaying marginal distributions along the axes of scatter plots
- Identifying potential outliers at the edges of a distribution

## Data

- `values` (numeric) - Continuous variable to display as tick marks
- Size: 5-1000+ observations (works well at any sample size)
- Example: Measurement data, response times, or any continuous variable

## Notes

- Use semi-transparency (alpha) when observations overlap
- Tick height should be consistent and small relative to the plot
- Position along x-axis by default, but can be placed on y-axis
- Works best as a complement to histograms, density plots, or scatter plots

## What a good version looks like

- A good version shows: one tick per observation at its exact value along the axis it sits on (the x axis by default, or the y axis as the Notes allow), drawn perpendicular to that axis.
- A good version shows: ticks of one consistent height, small relative to the plot, as the Notes ask, and visible against the page in both themes.
- A good version shows: semi-transparent ticks where observations overlap, as the Notes ask, so clusters read darker, with no tick moved along the value axis to separate it from its neighbors.
- A good version shows: the basic variant's rug: the ticks, besides the histogram, density curve or scatter plot the Notes allow it to complement, and no mean, median or other reference lines, highlighted ticks or bands, or callouts.
- Expected, not a defect: ticks that merge into solid bands in clusters, wide bare gaps, isolated ticks at the edges, and a mostly empty plot area beside a rug that stands alone.
