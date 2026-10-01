# lift-curve: Model Lift Chart

## Description

A lift curve visualizes how much better a predictive model performs compared to random selection, showing the cumulative lift ratio as you target increasing percentages of the population. It answers the question: "If I target the top X% of predictions, how many times more responders will I capture than random targeting?" This plot is essential for evaluating and comparing classification models in scenarios where targeting efficiency matters.

## Applications

- Marketing campaign targeting: Determine how many customers to contact for maximum response rate improvement
- Customer churn prediction: Identify high-risk customers to prioritize for retention efforts
- Fraud detection: Evaluate how effectively a model concentrates fraudulent cases in top-ranked predictions
- Direct mail optimization: Calculate the optimal mailing list size for cost-effective campaigns

## Data

- `y_true` (binary) - Actual outcomes (0 or 1), such as responded/not-responded or churned/retained
- `y_score` (float) - Predicted probabilities or scores from the model, higher values indicating higher likelihood
- Size: 100-10000 samples recommended for smooth curves
- Example: Customer response data with model probability scores and actual response flags

## Notes

- X-axis shows percentage of population targeted (0-100%)
- Y-axis shows cumulative lift ratio (model response rate / baseline response rate)
- Always include a horizontal reference line at y=1 representing random selection (no lift)
- Higher lift at lower percentages indicates better model discrimination
- Curve should start high and gradually approach 1 as percentage increases
- Consider showing decile markers or actual values at key percentiles

## What a good version looks like

- A good version shows: the cumulative lift ratio on the y axis against the percentage of the population targeted on the x axis, as the Notes ask, the curve drawn through its computed values and not smoothed.
- A good version shows: a horizontal reference line at a lift of 1 for random selection, as the Notes ask, running across the whole population axis, told apart from the model curve and visible in both themes.
- A good version shows: a curve that starts high and approaches the reference line as the percentage grows, as the Notes ask, meeting it where the whole population is targeted.
- A good version shows: a lift axis that holds both the reference line and the curve's highest value, so the height above random selection reads directly from the axis.
- A good version shows: decile markers or values at key percentiles, if drawn, sitting on the curve at their percentiles, with any value label matching the curve at that point.
- Expected, not a defect: an erratic first stretch where a few top-ranked cases decide the ratio, small wiggles along the descent, and a right end that lies almost flat on the reference line.
