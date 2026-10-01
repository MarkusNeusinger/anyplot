# bar-feature-importance: Feature Importance Bar Chart

## Description

A horizontal bar chart displaying feature importances from machine learning models, with features sorted by importance value and bars colored by a gradient to emphasize relative contribution. This visualization is essential for model interpretability, helping data scientists and stakeholders understand which features drive model predictions. The horizontal orientation allows for readable feature names of varying lengths.

## Applications

- Explaining random forest or gradient boosting model decisions to stakeholders
- Feature selection by identifying low-importance variables for removal
- Model debugging by detecting unexpected high-importance features that may indicate data leakage

## Data

- `feature` (categorical) - Names of the model features displayed on the y-axis
- `importance` (numeric) - Importance scores from the model, used for bar length
- `std` (numeric, optional) - Standard deviation of importance for ensemble methods, displayed as error bars
- Size: 10-30 features recommended for readability
- Example: Feature importances from sklearn RandomForestClassifier or XGBoost

## Notes

- Sort bars by importance value (highest at top) for easy identification of key features
- Use a sequential color gradient (e.g., light to dark) mapped to importance values
- Error bars are optional but valuable for ensemble methods showing importance variability
- Consider showing only top N features if the model has many features
- Include importance values as text annotations at the end of bars for precision

## What a good version looks like

- A good version shows: one horizontal bar per displayed feature, all features or the top ones the Notes allow, rising from a zero baseline to its importance, so bar length stays proportional to the score, with each name written out in full beside its bar.
- A good version shows: the bars sorted by importance with the highest at the top, as the Notes ask.
- A good version shows: a sequential color gradient mapped to the importance values, as the Notes ask, so color and bar length tell the same ranking, with the weakest bars still distinct from the page in both themes.
- A good version shows: the importance values as text at the end of the bars, as the Notes ask, each matching its bar's length and clear of any error bar.
- A good version shows: error bars, if drawn, centered on the end of each bar and visible against the bar's fill at every step of the gradient.
- Expected, not a defect: a few dominant features followed by a long tail of bars near zero, and error bars on small bars that reach down to or past zero.
