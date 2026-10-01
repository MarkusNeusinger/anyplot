# qq-basic: Basic Q-Q Plot

## Description

A Q-Q (Quantile-Quantile) plot compares the distribution of a dataset against a theoretical distribution (typically normal) or another dataset. Points are plotted by matching sample quantiles to theoretical quantiles, with a diagonal reference line indicating perfect distribution match. Deviations from the line reveal distribution characteristics such as skewness, heavy tails, and outliers.

## Applications

- Testing normality assumptions before parametric statistical tests (t-tests, ANOVA, regression)
- Identifying distribution characteristics such as skewness and kurtosis in research datasets
- Quality control analysis to verify process measurements follow expected distributions
- Detecting outliers and data quality issues in experimental data

## Data

- `sample` (numeric) - The observed data values to compare against the reference distribution
- Reference: Normal distribution (default) with parameters estimated from sample
- Size: 30-500 observations recommended for meaningful visual comparison

## Notes

- Points falling along the diagonal reference line indicate data follows the reference distribution
- Systematic deviations reveal specific distribution characteristics: S-curves indicate skewness, curved ends indicate heavy or light tails
- The 45-degree reference line (y=x) should be clearly visible
- Axis labels should indicate "Theoretical Quantiles" and "Sample Quantiles"

## What a good version looks like

- A good version shows: one point per observation, its sample quantile paired with the matching theoretical quantile of the reference distribution, every point at its computed quantiles and never jittered or smoothed.
- A good version shows: the diagonal reference line on which sample and theoretical quantiles are equal, clearly visible, as the Notes ask, running along the whole point pattern and distinct from the points in both themes.
- A good version shows: axis labels that indicate theoretical quantiles on one axis and sample quantiles on the other, as the Notes ask, with both tails of the point pattern inside the plot area.
- A good version shows: the basic variant's one sample against one reference distribution: besides the diagonal the Notes ask for, no confidence envelope, second sample or group, further reference lines, highlighted points or regions, callouts or statistic annotations, or marginal histograms.
- Expected, not a defect: points leaving the line in the tails, an S-shaped or bowed pattern for skewed or heavy-tailed data, a few outliers at either end and small wiggles around the line; these departures are what the plot is for.
