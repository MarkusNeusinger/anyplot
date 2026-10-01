# bar-permutation-importance: Permutation Feature Importance Plot

## Description

A horizontal bar chart displaying permutation feature importance from machine learning models, showing the decrease in model score when each feature is randomly shuffled. Unlike model-specific feature importances, permutation importance is model-agnostic and measures how much the model's performance degrades when a feature's relationship with the target is broken. Error bars indicate variability across multiple shuffles, providing a confidence measure for each importance score.

## Applications

- Comparing feature importance across different model types (e.g., comparing a random forest vs neural network on the same dataset)
- Identifying features that may be redundant or have spurious correlations by examining importance variability
- Model validation by verifying that domain-expected important features rank highly in permutation importance

## Data

- `feature` (categorical) - Names of the model features displayed on the y-axis
- `importance_mean` (numeric) - Mean decrease in model score across permutation repetitions
- `importance_std` (numeric) - Standard deviation of the score decrease, displayed as error bars
- Size: 10-30 features recommended for readability
- Example: Output from sklearn.inspection.permutation_importance with n_repeats=10

## Notes

- Sort bars by mean importance (highest at top) for easy identification of key features
- Include horizontal error bars to show importance variability across shuffles
- Use a sequential color gradient mapped to importance values for visual emphasis
- Add a vertical reference line at x=0 to distinguish positive from negative importance values
- Consider showing only top N features if the model has many features

## What a good version looks like

- A good version shows: one horizontal bar per feature from zero to its mean importance, a negative mean extending to the other side of zero, with every feature name written out in full beside its bar.
- A good version shows: the bars sorted by mean importance with the highest at the top, as the Notes ask.
- A good version shows: a horizontal error bar on every bar for the variability across shuffles, as the Notes ask, centered on the bar's end and visible against the bar's fill in both themes.
- A good version shows: a vertical reference line at zero, as the Notes ask, running the full height of the bars and visible in both themes, so positive and negative importances separate at a glance.
- A good version shows: a sequential color gradient mapped to the importance values, as the Notes ask, so color and bar length tell the same ranking, with the weakest bars still distinct from the page in both themes.
- Expected, not a defect: negative importances, error bars that cross zero, error bars of very different widths, and a long tail of features near zero.
