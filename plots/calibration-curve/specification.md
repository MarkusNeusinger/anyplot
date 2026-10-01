# calibration-curve: Calibration Curve

## Description

A calibration curve (reliability diagram) visualizes how well the predicted probabilities of a binary classifier match actual outcomes. By plotting the fraction of positives against mean predicted probability in binned intervals, it reveals whether a model is well-calibrated, overconfident, or underconfident. A perfectly calibrated model follows the diagonal line where predicted probability equals observed frequency.

## Applications

- Evaluating probability predictions in credit scoring models where accurate risk estimates determine loan pricing
- Assessing diagnostic confidence in medical screening systems where probability calibration affects treatment decisions
- Comparing calibration across multiple classifiers to select models that produce reliable probability estimates
- Validating risk assessment models in insurance and fraud detection where miscalibrated probabilities lead to financial losses

## Data

- `y_true` (binary array) - Ground truth binary labels (0 or 1)
- `y_prob` (numeric array) - Predicted probabilities from classifier (0 to 1)
- Size: 500-10000 samples recommended for reliable binning
- Example: Binary classification predictions from sklearn classifier with `predict_proba()` output

## Notes

- Include a diagonal reference line representing perfect calibration (predicted probability = observed frequency)
- Use 10 bins by default, with bin edges at equal probability intervals (0.0-0.1, 0.1-0.2, etc.)
- Display Brier score or Expected Calibration Error (ECE) as a summary metric
- Optional: include histogram of predicted probabilities as a secondary subplot to show prediction distribution
- For multiple models comparison, use distinct colors with clear legend

## What a good version looks like

- A good version shows: the fraction of positives on the y axis against the mean predicted probability on the x axis, the curve passing through each bin's computed pair of values, never smoothed, with the bins readable as individual points.
- A good version shows: the diagonal reference line of perfect calibration, as the Notes ask, on axes that share one probability scale, told apart from the model curves and visible in both themes.
- A good version shows: the Brier score or the Expected Calibration Error as a summary metric, as the Notes ask, in the legend, an annotation or the subtitle, placed so that it is clear which model it belongs to.
- A good version shows: the histogram of predicted probabilities the Notes allow, if drawn, as a secondary panel that shares the probability axis with the curve and stays smaller than it.
- A good version shows: when several models are compared, each curve in a distinct color and named in a legend, as the Notes ask.
- Expected, not a defect: a curve that leaves the diagonal in an S shape or an inverted S shape, points unevenly spaced along the x axis because predictions bunch, a jagged stretch where a bin holds few samples, and no point for an empty bin.
