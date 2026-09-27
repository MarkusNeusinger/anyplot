# scatter-basic: Basic Scatter Plot

## Description

A fundamental 2D scatter plot that displays the relationship between two numeric variables by plotting points on a Cartesian coordinate system. This visualization is essential for exploring correlations, identifying patterns, detecting outliers, and understanding the distribution of paired data points.

## Applications

- Analyzing the correlation between height and weight in a health study
- Exploring the relationship between marketing spend and sales revenue
- Investigating the connection between study hours and exam scores

## Data

- `x` (numeric) - Independent variable values plotted on the horizontal axis
- `y` (numeric) - Dependent variable values plotted on the vertical axis
- Size: 50-500 points recommended for clear visualization
- Example: Random correlated data with moderate positive correlation (r~0.7) and noise to demonstrate typical scatter patterns

## Notes

- Points should have moderate transparency (alpha ~0.7) to reveal overlapping data
- Include axis labels and a descriptive title
- Grid lines help with value estimation
- Consider point size that balances visibility with overlap clarity

## What a good version looks like

- A good version shows: one point per observation at its exact (x, y) value, all in one color, so the cloud's direction, spread and the odd outlier read at a glance.
- Expected, not a defect: points overlapping where the cloud is dense, visible noise around the trend and a few outliers.
- A good version shows: moderate transparency, so piled-up areas read darker, with no point jittered or nudged off its values to separate them.
- A good version shows: a cloud that scatters like real paired data; one lying exactly on a line suggests fabricated data.
- A good version shows: the basic variant's x and y only: no color or size channel, no regression or trend line, no marginal distributions and no point labels.
