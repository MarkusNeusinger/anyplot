# pdp-basic: Partial Dependence Plot

## Description

A partial dependence plot (PDP) showing the marginal effect of one feature on the predicted outcome of a machine learning model. The plot displays how predictions change as a feature varies across its range, while averaging over the effects of all other features. This visualization is essential for understanding the relationship between individual features and model predictions in interpretable machine learning.

## Applications

- Interpreting complex models like gradient boosting or random forests by revealing how features influence predictions
- Validating that learned relationships align with domain knowledge (e.g., higher prices lead to lower demand)
- Communicating model behavior to non-technical stakeholders by showing intuitive feature-response curves

## Data

- `feature_values` (numeric) - The range of values for the feature being analyzed on the x-axis
- `partial_dependence` (numeric) - The average predicted outcome for each feature value on the y-axis
- `confidence_interval` (numeric, optional) - Upper and lower bounds showing prediction variability across samples
- Size: 50-100 grid points along feature range recommended for smooth curves
- Example: PDP from sklearn's `PartialDependenceDisplay` for a feature in a GradientBoostingRegressor

## Notes

- The y-axis represents partial dependence (average prediction), not probability
- Include a confidence band or individual conditional expectation (ICE) lines for uncertainty visualization
- A rug plot along the x-axis can show the distribution of training data values
- Consider centering the partial dependence at zero for easier interpretation of relative effects
- For categorical features, use a bar or step plot instead of a continuous line

## What a good version looks like

- A good version shows: the partial dependence as one prominent line through the average prediction at every grid value across the feature's range, not smoothed beyond the grid; a categorical feature gets bars or steps instead, as the Notes ask.
- A good version shows: a confidence band or individual conditional expectation lines for the uncertainty, as the Notes ask, lighter than the partial dependence line and behind it, so the average stays the strongest mark in both themes.
- A good version shows: a y axis that reads as partial dependence, the average prediction, and not as a probability, as the Notes ask, and that says so when the curve is centered at zero as the Notes allow.
- A good version shows: the rug the Notes allow, if drawn, as short ticks along the x axis at the observed feature values, clear of the curve.
- A good version shows: the basic variant's one feature and one model: besides the band or ICE lines the Notes ask for and the rug and zero-centering they allow, no second feature, no reference or mean lines other than a zero line on a centered plot, no highlighted regions or points, no callouts and no second panel.
- Expected, not a defect: flat stretches, steps and kinks from a tree-based model, a curve that rises and falls, a band or ICE spread that changes width along the range, and ICE lines that cross each other.
