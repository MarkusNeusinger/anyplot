# precision-recall: Precision-Recall Curve

## Description

A Precision-Recall curve plots precision (positive predictive value) against recall (sensitivity) at various classification thresholds. This visualization is essential for evaluating binary classifiers on imbalanced datasets where accuracy alone is misleading. The area under the curve (Average Precision) summarizes classifier performance, with higher values indicating better performance.

## Applications

- Evaluating fraud detection models where fraudulent transactions are rare compared to legitimate ones
- Assessing medical diagnostic systems where correctly identifying positive cases (high recall) is critical
- Comparing information retrieval systems for document search relevance ranking
- Optimizing spam filters to balance catching spam (recall) with minimizing false positives (precision)

## Data

- `y_true` (binary array) - Ground truth binary labels (0 or 1)
- `y_scores` (numeric array) - Predicted probabilities or decision function scores from classifier
- Size: 100-10000 samples typical for evaluation
- Example: Binary classification predictions from sklearn classifier with `predict_proba()` output

## Notes

- Display Average Precision (AP) score in legend or annotation
- Include baseline reference line showing random classifier performance (horizontal line at positive class ratio)
- Use stepped line style to accurately represent threshold-based curve
- Consider showing iso-F1 curves as contour lines for F1 score reference
- For multiple classifiers comparison, use distinct colors with clear legend

## What a good version looks like

- A good version shows: precision on the y axis against recall on the x axis, the curve drawn as a stepped line, as the Notes ask, through its computed threshold points and never smoothed.
- A good version shows: the baseline of a random classifier as a horizontal line at the positive class ratio, as the Notes ask, not as a diagonal, told apart from the model curve and visible in both themes.
- A good version shows: the Average Precision score in the legend or an annotation, as the Notes ask, placed so that it is clear which curve it belongs to.
- A good version shows: iso-F1 curves, if drawn, as faint contour lines behind the precision-recall curve, each labeled with its F1 value and subordinate to the curve.
- A good version shows: when several classifiers are compared, each curve in a distinct color and named in a legend, as the Notes ask.
- Expected, not a defect: a sawtooth curve whose precision jumps up and down at low recall, a steep fall toward the baseline at high recall, and a baseline that sits far from the middle of the precision axis on imbalanced data.
