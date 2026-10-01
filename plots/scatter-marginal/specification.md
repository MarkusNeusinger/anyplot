# scatter-marginal: Scatter Plot with Marginal Distributions

## Description

A scatter plot enhanced with marginal distribution plots (histograms or kernel density estimates) on the top and right axes. This composite visualization simultaneously shows the bivariate relationship between two variables in the central scatter plot while displaying each variable's univariate distribution along its respective axis. It provides a comprehensive view of both the joint and marginal distributions in a single figure.

## Applications

- Exploring the correlation between two continuous variables while understanding their individual distributions in exploratory data analysis
- Visualizing feature relationships in machine learning datasets to identify skewness, multimodality, or outliers
- Analyzing measurement data in scientific research where both the relationship and the distribution characteristics matter

## Data

- `x` (numeric) - Independent variable values plotted on the horizontal axis
- `y` (numeric) - Dependent variable values plotted on the vertical axis
- Size: 50-1000 points recommended for clear visualization of both scatter and distributions
- Example: Random bivariate data with correlation to demonstrate typical patterns

## Notes

- Main scatter plot should be positioned in the lower-left with marginal plots aligned on top and right
- Marginal plots can be histograms, KDE curves, or both overlaid
- Axes of marginal plots must align with the main scatter plot axes
- Consider using subtle colors for marginal distributions to not distract from the main scatter plot
- Points should have moderate transparency (alpha ~0.6-0.7) to reveal density patterns

## What a good version looks like

- A good version shows: the scatter as the largest panel at the lower left, one point per observation at its exact (x, y) value, with the x distribution above it and the y distribution to its right, as the Notes ask.
- A good version shows: each marginal sharing its axis with the scatter, as the Notes require, so a peak in a marginal sits directly above or beside the points that cause it; the right marginal is drawn sideways, growing away from the scatter.
- A good version shows: marginals as histograms, density curves or both, as the Notes allow, rising from a zero baseline at the scatter's edge, in the points' own color or the quieter tone the Notes suggest, so the scatter stays the main panel.
- A good version shows: translucent points, as the Notes ask, so dense regions read darker and agree with the marginal peaks, and only a small gap between the three panels.
- Expected, not a defect: skewed, lumpy or two-peaked marginals, marginals of different shape for x and y, an empty corner at the top right, and marginal count axes with few or no tick labels.
