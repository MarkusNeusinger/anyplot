# density-basic: Basic Density Plot

## Description

A density plot (also known as Kernel Density Estimation or KDE plot) visualizes the distribution of a continuous variable by smoothing the data into a continuous probability density curve. Unlike histograms which use discrete bins, density plots provide a smooth representation of the underlying distribution, making it easier to identify patterns such as skewness, modality, and overall shape.

## Applications

- Visualizing the shape of a single variable's distribution for exploratory data analysis
- Identifying distribution characteristics like skewness, bimodality, or outliers
- Statistical analysis and exploratory data analysis in research
- Quality control monitoring to detect process shifts or anomalies

## Data

- `values` (numeric) - The continuous variable to visualize
- Size: 30-1000 observations recommended for meaningful density estimation
- Example: Heights, weights, test scores, response times, or any continuous measurement

## Notes

- Use a smooth curve representing probability density (area under curve equals 1)
- Consider adding fill under the curve with transparency for visual appeal
- Optional: include a rug plot showing individual observations along the x-axis
- Choose appropriate bandwidth (smoothing parameter) to balance detail and noise

## What a good version looks like

- A good version shows: one smooth curve of probability density over the value axis, as the Notes ask, on a density axis that starts at zero, with the curve falling back toward zero at both ends.
- A good version shows: a smoothing that fits the sample: modes and skew stay visible, without spiky noise and without everything merged into one flat hump.
- A good version shows: tails that end near the data range instead of trailing far beyond it.
- A good version shows: a fill under the curve, if drawn as the Notes suggest, transparent enough that gridlines and any rug stay visible through it, with the curve's outline still distinct in both themes.
- A good version shows: the basic variant's single density curve, with the fill and the rug the Notes allow, and no histogram bars, second group, mean, median or other reference lines, highlighted regions or bands, or callouts.
- Expected, not a defect: a skewed, two-peaked or lumpy curve, a long thin tail, and a curve that reaches slightly past the smallest and largest observations.
