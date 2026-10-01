# scatter-regression-linear: Scatter Plot with Linear Regression

## Description

A scatter plot that displays the relationship between two numeric variables with a fitted linear regression line and confidence interval band. This visualization extends the basic scatter plot by adding statistical modeling elements, making it ideal for understanding linear relationships, assessing model fit, and communicating the strength of correlations with visual uncertainty quantification.

## Applications

- Analyzing the relationship between advertising spend and sales revenue with prediction confidence
- Studying the correlation between study hours and exam scores in educational research
- Investigating the linear relationship between temperature and energy consumption in utility planning

## Data

- `x` (numeric) - Independent variable values plotted on the horizontal axis
- `y` (numeric) - Dependent variable values plotted on the vertical axis
- Size: 30-300 points recommended for clear regression visualization
- Example: Correlated data with noise to demonstrate regression fit and confidence intervals

## Notes

- Display R² or correlation coefficient (r) prominently on the plot
- Regression line should be visually distinct from scatter points (solid line, contrasting color)
- Confidence band should use semi-transparent shading (95% CI recommended)
- Points should have moderate transparency (alpha ~0.6-0.7) to show density
- Include axis labels and descriptive title mentioning the regression analysis
- Consider adding the regression equation (y = mx + b) as annotation

## What a good version looks like

- A good version shows: every observation as a translucent point at its exact (x, y) value, as the Notes ask, with one straight fitted line drawn over the points, solid and in a color that contrasts with them.
- A good version shows: a semi-transparent confidence band around the line, as the Notes ask, narrowest near the middle of the data and widening toward both ends, light enough that the points inside it remain visible.
- A good version shows: R² or the correlation coefficient stated on the plot, as the Notes ask, and the regression equation, if added, both placed where they cover neither points nor line, with a sign that agrees with the drawn slope.
- A good version shows: a title that mentions the regression, as the Notes ask, and a legend or annotation that says what the band is, for instance the 95 percent confidence interval the Notes recommend.
- Expected, not a defect: many points lying outside the confidence band, which bounds the fitted line and not the individual observations, visible scatter around the line, and a few outliers.
