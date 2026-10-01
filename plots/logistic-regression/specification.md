# logistic-regression: Logistic Regression Curve Plot

## Description

A logistic regression visualization showing the characteristic S-shaped (sigmoid) probability curve for binary classification. The plot displays data points colored by their binary class, the fitted logistic curve representing predicted probabilities, confidence intervals around the curve, and an optional decision threshold line. This visualization is essential for understanding how a logistic model maps continuous input features to class probabilities.

## Applications

- Visualizing credit risk scoring models where the probability of default varies with income or credit score
- Analyzing medical diagnostic thresholds where probability of disease changes with biomarker levels
- Understanding marketing conversion rates as a function of customer engagement metrics or ad spend
- Demonstrating the decision boundary in binary classification problems for educational purposes

## Data

- `x` (numeric) - Continuous independent variable (predictor/feature) plotted on the horizontal axis
- `y` (binary) - Binary outcome variable (0 or 1) plotted as data points
- `probability` (numeric) - Predicted probability from the logistic model (0 to 1) for the fitted curve
- Size: 50-500 data points recommended for clear visualization of both the curve and underlying data
- Example: Binary classification data where the outcome probability follows a sigmoidal relationship with the predictor

## Notes

- Data points should be jittered slightly on the y-axis (around 0 and 1) for visibility when overlapping
- Use distinct colors for the two classes (e.g., blue for class 0, orange for class 1)
- The logistic curve should be smooth and prominently displayed (solid line, ~2px width)
- Include 95% confidence interval band around the fitted curve with semi-transparent shading
- Add a horizontal dashed line at probability = 0.5 to indicate the default decision threshold
- Label axes clearly: x-axis with the predictor name, y-axis as "Probability" (0 to 1)
- Consider displaying model coefficients or accuracy metrics as annotations
- Points should have moderate transparency (alpha ~0.6) to show density patterns

## What a good version looks like

- A good version shows: the observations as points at their exact x values in two rows, one near each end of the probability axis, jittered slightly along the y axis only and in a distinct color per class, as the Notes ask.
- A good version shows: moderate transparency on the points, as the Notes ask, so stretches of x where many observations pile up read darker.
- A good version shows: the fitted curve as a smooth, solid and prominent line, as the Notes ask, S-shaped, staying inside the probability range and not hidden by the points or the band.
- A good version shows: a semi-transparent confidence band around the fitted curve, as the Notes ask, that encloses the curve at every x and leaves the points and gridlines visible through it in both themes.
- A good version shows: a horizontal dashed line at probability 0.5 for the default decision threshold, as the Notes ask, running across the whole x range and subordinate to the fitted curve.
- Expected, not a defect: the two classes overlapping along x in the middle of the range, single points far on the other class's side, a band that widens toward the ends where data is sparse, and a curve that reaches neither end of the probability range inside the plot.
