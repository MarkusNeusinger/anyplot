# diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)

## Description

A 2x2 panel of diagnostic plots for evaluating linear regression model assumptions, replicating the classic output of R's `plot(lm)`. The four subplots are: (1) Residuals vs Fitted values to detect non-linearity and heteroscedasticity, (2) Normal Q-Q plot of standardized residuals to assess normality, (3) Scale-Location plot (square root of standardized residuals vs fitted values) to check homoscedasticity, and (4) Residuals vs Leverage with Cook's distance contours to identify influential observations. This composite display is the standard first step in regression model validation across statistics, academia, and regulated industries.

## Applications

- Validating linear regression assumptions before reporting results in statistical analysis
- Checking for heteroscedasticity, non-linearity, and influential outliers in fitted models
- Teaching regression diagnostics in academic statistics courses and textbooks
- Regulatory model validation in finance (credit risk models) and pharma (dose-response modeling)

## Data

- `fitted` (float) - Fitted/predicted values from the regression model
- `residuals` (float) - Raw residuals (observed minus predicted)
- `std_residuals` (float) - Standardized (or studentized) residuals
- `leverage` (float) - Hat values / leverage for each observation
- `cooks_d` (float) - Cook's distance measuring each observation's influence
- Size: 50-500 observations

## Notes

- Four subplots arranged in a 2x2 grid layout with shared figure title
- **Subplot 1 (Residuals vs Fitted):** Scatter of residuals against fitted values with a horizontal zero-reference line and a LOWESS smoother to reveal non-linear patterns
- **Subplot 2 (Normal Q-Q):** Standardized residuals plotted against theoretical normal quantiles with a 45-degree reference line; deviations indicate non-normality
- **Subplot 3 (Scale-Location):** Square root of absolute standardized residuals vs fitted values with a LOWESS smoother; a flat line indicates constant variance
- **Subplot 4 (Residuals vs Leverage):** Standardized residuals vs leverage with Cook's distance contour lines (e.g., at 0.5 and 1.0) to highlight influential points
- Label the 2-3 most influential points (highest Cook's distance) with observation indices in each subplot
- Use consistent point styling across all four subplots

## What a good version looks like

- A good version shows: four panels in a 2x2 grid under one shared figure title, as the Notes ask (residuals against fitted values, normal Q-Q, scale-location, and residuals against leverage), each named, with the same point styling in all four.
- A good version shows: in the residuals-against-fitted panel a horizontal zero line and a LOWESS smoother, and in the scale-location panel the square root of the absolute standardized residuals with a LOWESS smoother, as the Notes ask, each smoother following its own points.
- A good version shows: in the Q-Q panel the standardized residuals against theoretical normal quantiles with a 45-degree reference line, as the Notes ask, every point at its computed quantiles.
- A good version shows: in the leverage panel the standardized residuals against leverage with Cook's distance contour lines, as the Notes ask, mirrored above and below zero, closing in on it as leverage grows, and identifiable by their level.
- A good version shows: the few most influential observations, those with the highest Cook's distance, labeled with their observation index in every panel, as the Notes ask, each label beside its own point.
- Expected, not a defect: a smoother that bends at the sparse ends of the fitted range, Q-Q points leaving the line in the tails, a scale-location trend that is not flat, points crowded at low leverage with a few far out, and labeled points that lie inside the Cook's distance contours.
