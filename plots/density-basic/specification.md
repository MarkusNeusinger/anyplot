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
