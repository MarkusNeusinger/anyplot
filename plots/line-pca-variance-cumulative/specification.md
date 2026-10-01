# line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection

## Description

A line plot showing the cumulative proportion of explained variance as a function of the number of Principal Component Analysis (PCA) components. This visualization helps determine the optimal number of components to retain by displaying the trade-off between dimensionality reduction and information preservation. The cumulative curve typically exhibits an elbow pattern where additional components yield diminishing returns, and horizontal threshold lines (e.g., 90%, 95%) guide component selection decisions.

## Applications

- Dimensionality reduction: choosing how many PCA components to retain for downstream machine learning tasks
- Feature engineering: determining the optimal reduced feature space size while preserving target variance thresholds
- Data compression: evaluating information loss vs. computational efficiency trade-offs in high-dimensional data
- Exploratory data analysis: understanding the intrinsic dimensionality and complexity of multivariate datasets

## Data

- `explained_variance_ratio` (numeric array) - proportion of variance explained by each individual component (sums to 1.0)
- `n_components` (integer) - number of PCA components (x-axis values from 1 to total components)
- Size: typically 5-50 components depending on original feature count
- Example: scikit-learn's `PCA.explained_variance_ratio_` attribute

## Notes

- Display cumulative sum on y-axis, not individual variance per component
- Y-axis should show percentage (0-100%) or proportion (0.0-1.0)
- Add horizontal dashed reference lines at common thresholds: 90%, 95%, and optionally 99%
- Mark or annotate the elbow point if automatically detectable
- Use clear markers at each component count to show discrete values
- Consider including individual variance ratios as a secondary bar plot overlay (optional enhancement)
- X-axis should start at 1 (first component), not 0

## What a good version looks like

- A good version shows: the cumulative explained variance, not the variance of each single component, as the Notes ask, as a curve that never falls from one component count to the next.
- A good version shows: a clear marker at every component count, as the Notes ask, each at its own cumulative value, on an x axis that starts at the first component and has whole-number ticks.
- A good version shows: horizontal dashed reference lines at the 90 and 95 percent thresholds, as the Notes ask, and at 99 percent if that optional line is drawn, each identified by a label or the legend and visible in both themes.
- A good version shows: the elbow point marked or annotated where one can be detected, as the Notes ask, on the curve's own marker for that component count.
- A good version shows: the individual variance ratios, if drawn as the bar overlay the Notes allow, as bars behind the cumulative curve that stay subordinate to it and are named in the legend or on their own axis.
- Expected, not a defect: a steep rise followed by a long flat approach to the full variance, thresholds crossed between two component counts, reference lines that sit close together near the top of the plot, and a curve with no sharp elbow.
