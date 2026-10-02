# gain-curve: Cumulative Gains Chart

## Description

A cumulative gains chart visualizes the effectiveness of a classification model by showing what percentage of positive cases is captured when targeting increasing percentages of the population, ranked by predicted probability. It answers the question: "If I target the top X% of my predictions, what percentage of all actual positives will I capture?" This plot is essential for evaluating targeting strategies in marketing, risk assessment, and resource allocation scenarios.

## Applications

- Marketing campaign optimization: Determine the minimum audience size needed to reach a target percentage of likely responders
- Customer churn prevention: Identify the smallest segment of at-risk customers that captures most potential churners
- Credit scoring model assessment: Evaluate how effectively a model concentrates defaulters in high-risk score bands
- Fraud detection prioritization: Calculate what fraction of investigations captures most fraudulent cases

## Data

- `y_true` (binary) - Actual outcomes (0 or 1), such as responded/not-responded or fraudulent/legitimate
- `y_score` (float) - Predicted probabilities or scores from the model, higher values indicating higher likelihood of positive class
- Size: 100-10000 samples recommended for smooth curves
- Example: Customer response data with model probability scores and actual conversion flags

## Notes

- X-axis shows percentage of population targeted (0-100%), sorted by predicted probability descending
- Y-axis shows cumulative percentage of positive cases captured (0-100%)
- Always include a diagonal reference line representing random selection (baseline model)
- A perfect model would show a steep straight line from the origin that reaches 100% at the positive class rate, then horizontal
- Steeper initial slope indicates better model discrimination
- Often displayed alongside lift curves for comprehensive model evaluation

## What a good version looks like

- A good version shows: the cumulative percentage of positive cases captured on the y axis against the percentage of the population targeted on the x axis, as the Notes ask, both axes running over their full range from none to all.
- A good version shows: the model curve starting at the origin and ending at the top-right corner, never falling, drawn through its computed points and not smoothed.
- A good version shows: the diagonal reference line of random selection, as the Notes ask, running from corner to corner, told apart from the model curve and visible in both themes.
- A good version shows: the perfect-model curve the Notes describe, if drawn, reaching full capture at the positive class rate and flat from there, and named so that it is not mistaken for the model.
- A good version shows: a legend or direct labels that tell the model curve from the random baseline.
- Expected, not a defect: a curve that rises steeply and then flattens, small steps or kinks from a finite sample, a curve that meets the diagonal at both corners, and a companion lift chart beside it.
