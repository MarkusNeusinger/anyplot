# coefficient-confidence: Coefficient Plot with Confidence Intervals

## Description

A coefficient plot displays regression coefficients as points positioned along a horizontal axis, with horizontal error bars showing confidence intervals. This visualization makes it easy to assess effect sizes and statistical significance - coefficients whose confidence intervals cross zero are not statistically significant. Typically used to summarize results from linear, logistic, or other regression models in a clear, publication-ready format.

## Applications

- Visualizing effect sizes and significance from multiple regression models
- Comparing predictor importance in linear or logistic regression analysis
- Presenting regression results in academic publications and reports
- Communicating which variables have significant effects in statistical models

## Data

- `variable` (str) - Name of the predictor variable or coefficient
- `coefficient` (float) - Point estimate of the regression coefficient
- `ci_lower` (float) - Lower bound of the confidence interval
- `ci_upper` (float) - Upper bound of the confidence interval
- `significant` (bool, optional) - Whether the coefficient is statistically significant
- Size: 5-20 coefficients for optimal readability
- Example: Coefficients from a multiple linear regression predicting housing prices

## Notes

- Vertical reference line at zero to indicate the null hypothesis threshold
- Variables typically ordered by coefficient magnitude for easier comparison
- Use different colors or markers to distinguish significant vs non-significant coefficients
- Horizontal layout (coefficients on y-axis, values on x-axis) preferred for readability with long variable names
- Include axis label indicating the effect measure (e.g., "Coefficient Estimate", "Log Odds Ratio")

## What a good version looks like

- A good version shows: one point per coefficient at its estimate, with a horizontal interval line through it from the lower to the upper confidence bound, variables listed down the vertical axis in the layout the Notes prefer, and no point moved off its estimate.
- A good version shows: a vertical reference line at zero, as the Notes ask, running the full height of the rows, visible in both themes and distinct from any gridline, so intervals that cross it stand apart from those that clear it.
- A good version shows: significant and non-significant coefficients told apart by color or marker, as the Notes ask, named in a legend or note, and agreeing with the data's significance flag where it is given, otherwise with whether each interval crosses zero.
- A good version shows: variables in a meaningful order, typically by coefficient magnitude as the Notes suggest, each named in full at its own row.
- A good version shows: a value axis whose label names the effect measure, as the Notes ask, such as a coefficient estimate or a log odds ratio.
- Expected, not a defect: intervals of very different width, intervals that cross the zero line, coefficients on both sides of zero, several small coefficients beside one or two large ones, and a value axis that is not symmetric about zero.
