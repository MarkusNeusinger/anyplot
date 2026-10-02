# histogram-2d: 2D Histogram Heatmap

## Description

A two-dimensional histogram that displays the joint distribution of two continuous variables as a heatmap with rectangular bins. Each bin's color intensity represents the frequency or count of data points falling within that region, making it ideal for revealing density patterns, clusters, and correlations in bivariate data. Unlike scatter plots that can become cluttered with large datasets, 2D histograms effectively summarize point density.

## Applications

- Analyzing joint distributions of financial returns across different asset classes
- Visualizing particle collision data density in physics experiments
- Exploring the relationship between customer age and purchase frequency in market research
- Identifying spatial density patterns in geographic coordinate data

## Data

- `x` (numeric) - continuous values for the horizontal axis
- `y` (numeric) - continuous values for the vertical axis
- Size: 500-100,000+ points (designed for datasets where scatter plots become unreadable)
- Example: Bivariate normal distribution with correlation

## Notes

- Include a colorbar to show the density/count scale
- Use a perceptually uniform colormap (e.g., viridis) for accurate density interpretation
- Bins parameter controls resolution (more bins = finer detail but noisier)
- Consider log scale for color mapping when density varies widely
- Optional: add marginal 1D histograms on top and right edges for univariate context

## What a good version looks like

- A good version shows: rectangular bins on a regular grid aligned with both axes, tiling the plot without gaps, each colored by the number of points that fall inside it.
- A good version shows: a sequential, perceptually uniform colormap, as the Notes ask, with a color bar labeled as a count or density, or as a log count when the log scale the Notes suggest is applied, and low-count bins that remain distinguishable from the page in both themes.
- A good version shows: a bin count that fits the sample: fine enough to show the shape and tilt of the joint distribution, coarse enough that the dense region reads as a gradient rather than salt-and-pepper noise.
- A good version shows: marginal histograms, if drawn as the Notes allow, on the top and right edges, each sharing its axis with the heatmap so its bars sit over the bins they summarize.
- Expected, not a defect: empty bins at the fringes, drawn blank or in the lowest color, uneven counts between neighboring bins in the tails, and a few isolated low-count bins from outlying points.
