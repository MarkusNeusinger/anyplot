# histogram-kde: Histogram with KDE Overlay

## Description

A histogram with kernel density estimate (KDE) overlay combines discrete binning with continuous density estimation to visualize the distribution of continuous data. The histogram bars show frequency counts in each bin while the smooth KDE curve reveals the underlying probability density, making it easier to perceive the true shape of the distribution without binning artifacts.

## Applications

- Analyzing financial return distributions to identify skewness and tail behavior
- Exploring measurement data in quality control to compare observed frequencies with theoretical distributions
- Understanding customer behavior patterns in marketing analytics with both discrete counts and smooth trends

## Data

- `values` (numeric) - The continuous variable to visualize
- Size: 50-1000 observations recommended for meaningful KDE estimation
- Example: Stock returns, test scores, sensor measurements, or any continuous distribution

## Notes

- Use semi-transparent histogram bars (alpha ~0.5) so the KDE curve remains visible
- Scale y-axis as density (not counts) so histogram and KDE are on comparable scales
- Choose appropriate bin count and KDE bandwidth to balance detail and smoothness
- Consider contrasting colors for histogram fill and KDE line for clear distinction

## What a good version looks like

- A good version shows: contiguous histogram bars on a y axis scaled as density, as the Notes ask, with a smooth KDE curve drawn over them on that same scale, so the curve runs at the level of the bar tops.
- A good version shows: semi-transparent bars, as the Notes ask, so the KDE curve stays visible along its whole length in both themes.
- A good version shows: a curve that reads as its own layer, in the contrasting color the Notes suggest or otherwise clearly set apart from the bar fill.
- A good version shows: a bin count and a smoothing that agree: the curve follows the histogram's modes and skew without flattening real peaks or chasing single bars.
- A good version shows: a curve whose tails end near the data range instead of trailing far beyond the outermost bars.
- Expected, not a defect: a curve that misses individual bar tops, bridges empty bins and reaches slightly past the outermost bars, over a lumpy, skewed or two-peaked histogram.
