# histogram-density: Density Histogram

## Description

A density histogram displays the distribution of a continuous variable normalized so that the total area under the histogram equals 1, representing probability density instead of raw counts. This normalization allows direct comparison between distributions with different sample sizes and enables overlaying theoretical probability density functions (PDFs) for statistical analysis.

## Applications

- Comparing empirical distributions across datasets with different sample sizes
- Overlaying theoretical distributions (normal, exponential, etc.) to assess goodness of fit
- Visualizing probability density for statistical inference and hypothesis testing
- Standardizing distribution displays for publication-quality statistical graphics

## Data

- `values` (numeric) - The continuous variable to visualize
- Size: 50-1000 observations recommended for meaningful density estimation
- Example: Test scores, measurement data, financial returns, or any continuous distribution

## Notes

- Y-axis shows density (probability per unit), not count
- Total area under histogram bars equals 1
- Bin width affects visual interpretation; use consistent binning for comparisons
- Consider adding a reference line or theoretical PDF overlay for context

## What a good version looks like

- A good version shows: contiguous bars over consistent bins with no gaps between them, each rising from a zero baseline to its bin's density, on a y axis labeled as density, not count, as the Notes ask.
- A good version shows: bar heights scaled so the bar areas sum to 1, as the Notes ask, so the axis values follow from the unit of the x axis and do not read as counts or shares of the sample.
- A good version shows: a theoretical density curve or reference line, if drawn as the Notes suggest, on the same density scale as the bars, drawn over them in a contrasting style and identified by a legend or label.
- A good version shows: a bin count that fits the sample: enough bins to show skew, clusters and tails, and not so many that the outline breaks into isolated spikes.
- Expected, not a defect: density values above 1 when the data spans a narrow range, a lumpy or skewed outline with empty bins in the tails, and bars that rise above or fall below an overlaid theoretical curve.
