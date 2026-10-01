# area-stacked-confidence: Stacked Area Chart with Confidence Bands

## Description

A stacked area chart that displays multiple data series as cumulative areas, with each series surrounded by uncertainty or confidence bands. This visualization combines the composition insight of stacked areas with the statistical rigor of confidence intervals, making it ideal for showing how parts contribute to a whole while simultaneously communicating uncertainty in each component. The bands reveal where estimates are precise versus uncertain across the stacked series.

## Applications

- Forecasting market share by competitor with prediction intervals
- Displaying portfolio allocation over time with risk bands for each asset class
- Showing energy consumption breakdown by source with measurement uncertainty
- Visualizing population projections by age group with demographic uncertainty

## Data

- `x` (datetime/numeric) - continuous axis values, typically time periods
- `y1, y2, y3, ...` (numeric) - central values for each series to be stacked
- `y1_lower, y1_upper, ...` (numeric) - lower and upper bounds of confidence bands for each series
- `category` (categorical) - labels identifying each series
- Size: 20-100 time points, 2-5 series
- Example: quarterly revenue forecasts by product line with 90% prediction intervals

## Notes

- Use distinct colors for each series, with matching lighter shades for confidence bands
- Semi-transparent fills (alpha 0.2-0.4) for bands to show overlap without obscuring data
- Stack order should be consistent between central values and their bands
- Consider using gradient fills from lower to upper bound for visual clarity
- Include legend identifying each series and what the bands represent
- Bands should be symmetric around each series or explicitly labeled if asymmetric

## What a good version looks like

- A good version shows: each series as a filled layer that starts where the layer below ends, the lowest from a zero baseline, with its stacked central value drawn as a distinct edge or line, so layer thickness reads as the series' value.
- A good version shows: around each series' stacked edge a band from its lower to its upper bound, in a lighter shade of that series' color and semi-transparent, as the Notes ask, so the layers and neighboring bands behind it stay visible in both themes.
- A good version shows: the same stack order for the central values and their bands at every x, as the Notes ask, so each band sits on its own series' edge and follows it along the axis.
- A good version shows: bands symmetric around their series' edge, or explicitly labeled as asymmetric when they are not, as the Notes ask.
- A good version shows: a legend that identifies each series and says what the bands represent, as the Notes ask.
- Expected, not a defect: bands that reach into the layers above and below and overlap neighboring bands, bands of different width between series or widening along the axis, and thin layers for small series.
