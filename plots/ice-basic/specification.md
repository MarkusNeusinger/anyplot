# ice-basic: Individual Conditional Expectation (ICE) Plot

## Description

An Individual Conditional Expectation (ICE) plot visualizes how the predicted outcome of a machine learning model changes for each individual observation as a single feature varies across its range. Unlike partial dependence plots (PDP) that show the average marginal effect, ICE plots display one line per observation, revealing heterogeneous effects, feature interactions, and subgroup-specific behaviors that would be hidden by averaging. This makes ICE plots essential for detecting when a feature's effect varies across the population.

## Applications

- Detecting feature interactions in ensemble models by identifying observations whose prediction curves diverge from the average trend
- Identifying subgroups with different feature responses in clinical prediction models, such as patients who respond differently to dosage changes
- Validating monotonicity assumptions in pricing or risk models by checking whether all individual curves move in the expected direction
- Exploring non-linear and heterogeneous effects in gradient boosting or random forest models during model audit and interpretability review

## Data

- `feature_value` (float) - Grid of values for the feature of interest, spanning its observed range on the x-axis
- `prediction` (float) - Model-predicted outcome for each observation at each grid point on the y-axis
- `observation_id` (int) - Unique identifier for each observation, defining individual ICE lines
- Size: 50-200 observations with 50-100 grid points per observation
- Example: ICE curves from a GradientBoostingRegressor showing how house price predictions change as square footage varies for individual houses

## Notes

- Individual lines should use low alpha (semi-transparent) to show density and overlap patterns
- Overlay the partial dependence (PDP) line as a bold, opaque curve to show the average effect
- Consider a centered ICE (c-ICE) variant that shifts all lines to start at zero for easier comparison of effect shapes
- A rug plot along the x-axis can indicate the distribution of observed feature values
- Color-coding lines by a second feature can help reveal interaction effects
- Complements the existing `pdp-basic` spec by showing individual-level detail behind the average
