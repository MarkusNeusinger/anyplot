# scatter-regression-polynomial: Scatter Plot with Polynomial Regression

## Description

A scatter plot displaying the relationship between two numeric variables with a fitted polynomial regression curve (degree 2-4). This visualization extends beyond linear regression to capture non-linear relationships in data, making it ideal for modeling curved trends, parabolic patterns, and complex data relationships where a straight line would not adequately represent the underlying pattern.

## Applications

- Analyzing diminishing returns in economics where initial gains decrease over time
- Studying growth curves in biology where populations follow sigmoid or exponential patterns
- Modeling physical phenomena like projectile motion or thermal expansion with quadratic relationships

## Data

- `x` (numeric) - Independent variable values plotted on the horizontal axis
- `y` (numeric) - Dependent variable values plotted on the vertical axis following a non-linear relationship
- Size: 30-300 points recommended for clear polynomial curve visualization
- Example: Data with a clear curved pattern such as quadratic, cubic, or sigmoid trends

## Notes

- Display R² value prominently on the plot to indicate goodness of fit
- Polynomial curve should be visually distinct from scatter points (solid line, contrasting color)
- Use polynomial degree 2 (quadratic) as default; higher degrees (3-4) for more complex curves
- Optional: Include confidence band with semi-transparent shading around the fitted curve
- Points should have moderate transparency (alpha ~0.6-0.7) to show density
- Include axis labels and descriptive title mentioning polynomial regression
- Consider annotating with the polynomial equation (y = ax² + bx + c)
- Avoid overfitting: higher-degree polynomials should only be used when justified by data pattern

## What a good version looks like

- A good version shows: every observation as a translucent point at its exact (x, y) value, as the Notes ask, with one solid fitted curve in a contrasting color, drawn smoothly rather than as straight segments with visible kinks between the data points.
- A good version shows: a curve whose number of bends fits the visible pattern, quadratic by default as the Notes say: it follows the cloud's curvature without extra wiggles between points or wild swings at the ends of the x range.
- A good version shows: R² stated on the plot, as the Notes ask, and the polynomial equation, if annotated, both placed clear of points and curve, with a title that mentions the polynomial regression, as the Notes ask.
- A good version shows: the confidence band, if drawn as the Notes allow, semi-transparent around the curve and widening toward the ends of the x range, with the points inside it still visible.
- Expected, not a defect: points scattered on both sides of the curve along its whole length, many of them outside the confidence band, and a few outliers the curve does not pass through.
