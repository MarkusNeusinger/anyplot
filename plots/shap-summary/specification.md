# shap-summary: SHAP Summary Plot

## Description

A SHAP (SHapley Additive exPlanations) summary plot displaying the distribution of SHAP values for each feature, ordered by mean absolute SHAP value (importance). Each dot represents a sample, positioned horizontally by its SHAP value and colored by the feature's value (typically low=blue to high=red). This visualization is essential for machine learning interpretability, showing both feature importance and the direction and magnitude of feature effects on model predictions.

## Applications

- Explaining gradient boosting or random forest model predictions to stakeholders by showing which features drive predictions up or down
- Identifying non-linear relationships where high and low feature values both push predictions in the same direction
- Detecting feature interactions by observing clustered or bimodal SHAP value distributions

## Data

- `shap_values` (numeric matrix) - SHAP values for each sample and feature, shape (n_samples, n_features)
- `feature_values` (numeric matrix) - Original feature values for coloring, same shape as shap_values
- `feature_names` (categorical) - Names of features for y-axis labels
- Size: 100-1000 samples recommended for clear distributions
- Example: SHAP values from shap.TreeExplainer on XGBoost/LightGBM model

## Notes

- Sort features by mean absolute SHAP value (most important at top)
- Use diverging color scale (blue-red) to indicate low-to-high feature values
- Add vertical line at x=0 to clearly separate positive and negative impacts
- Consider jittering points vertically to reduce overlap
- For many features, show only top 10-20 most important

## What a good version looks like

- A good version shows: one row per feature shown (all of them, or only the most important ones where there are many, as the Notes allow), labeled with the feature name and sorted by mean absolute SHAP value with the most important feature at the top, as the Notes ask.
- A good version shows: in every row one dot per sample at its SHAP value on the horizontal axis; vertical spread inside a row, where used as the Notes suggest, is layout only, so dots pile up where SHAP values are dense and stay within their own row.
- A good version shows: every dot colored by its feature's value on a diverging blue-to-red scale from low to high, as the Notes ask, with a color bar marking the low and the high end, and mid-scale dots still visible against the page in both themes.
- A good version shows: a vertical line at a SHAP value of zero, as the Notes ask, visible in both themes without covering the dots, so positive and negative impacts separate at a glance.
- Expected, not a defect: rows of very different width, from widely spread top features to tight clumps at zero, dots that overlap where a row is dense, lopsided rows, separate clumps for a binary feature, and both colors mixed on one side of zero.
