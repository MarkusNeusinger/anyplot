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
