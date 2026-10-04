# bland-altman-basic: Bland-Altman Agreement Plot

## Description

A Bland-Altman plot (also known as a difference plot or Tukey mean-difference plot) visualizes the agreement between two measurement methods by plotting the difference against the average of paired observations. It displays the mean difference (bias) as a horizontal line and limits of agreement (mean ± 1.96 SD) to assess whether the methods are interchangeable within acceptable tolerances.

## Applications

- Comparing a new blood glucose meter against a laboratory reference standard in medical device validation
- Assessing inter-rater reliability between two observers measuring the same physiological parameter
- Evaluating whether two analytical chemistry methods produce equivalent results for quality control

## Data

- `method1` (numeric) - Measurements from the first method or observer
- `method2` (numeric) - Corresponding measurements from the second method or observer
- Size: 30-200 paired observations recommended for reliable limits of agreement estimation
- Example: Paired blood pressure readings from two different sphygmomanometers on the same subjects

## Notes

- The x-axis shows the mean of each pair: (method1 + method2) / 2
- The y-axis shows the difference: method1 - method2
- Include a horizontal line at the mean difference (bias)
- Include dashed horizontal lines at ±1.96 SD (95% limits of agreement)
- Annotate the mean and limits of agreement values on the plot
- Optional: a zero-difference line and confidence intervals of the bias and of the limits of agreement
- Points should have moderate transparency to reveal overlapping observations

## What a good version looks like

- A good version shows: one point per pair, at the mean of the two methods on the x axis and at their difference (first method minus second) on the y axis, as the Notes define them, never jittered or displaced.
- A good version shows: a horizontal line at the mean difference and dashed horizontal lines at the two limits of agreement, as the Notes ask, each at its computed value, the limits equally far above and below the bias line, all three visible in both themes.
- A good version shows: the values of the mean difference and of both limits of agreement annotated on the plot, as the Notes ask, each matching its line and attributable to it.
- A good version shows: moderate transparency on the points, as the Notes ask, so that overlapping observations read darker.
- A good version shows: the basic variant's one method pair: besides the bias, limit lines and value labels the Notes ask for, only the zero line and confidence intervals of bias and limits they allow; no other reference lines, trend line, a tinted zone between the limits, highlighted points, callouts or marginal plots.
- Expected, not a defect: a few points outside the limits of agreement, a bias line that sits away from zero, and a scatter that widens or drifts as the mean grows; these are what the plot is meant to reveal.
