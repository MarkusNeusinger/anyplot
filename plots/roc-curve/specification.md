# roc-curve: ROC Curve with AUC

## Description

A Receiver Operating Characteristic (ROC) curve visualizes the performance of a binary classifier by plotting the True Positive Rate (TPR) against the False Positive Rate (FPR) at various classification thresholds. The Area Under the Curve (AUC) provides a single metric summarizing model performance, where 1.0 indicates perfect classification and 0.5 represents random guessing.

## Applications

- Evaluating binary classification model performance in machine learning pipelines
- Comparing multiple models to select the best classifier for production
- Selecting optimal classification thresholds based on sensitivity/specificity trade-offs
- Assessing diagnostic test accuracy in medical research

## Data

- `fpr` (numeric) - False Positive Rate values (0 to 1)
- `tpr` (numeric) - True Positive Rate values (0 to 1)
- `auc` (numeric) - Area Under the Curve score (0 to 1)
- Size: typically 100-1000 threshold points per curve
- Example: sklearn.metrics.roc_curve output from binary classification predictions

## Notes

- Include a diagonal reference line (y=x) representing random classifier performance
- Display AUC score in legend or annotation
- Use distinct colors/styles when comparing multiple models
- Axes should range from 0 to 1 with equal aspect ratio preferred

## What a good version looks like

- A good version shows: the true positive rate on the y axis against the false positive rate on the x axis, each curve running from the bottom-left corner to the top-right corner through its computed operating points, never smoothed.
- A good version shows: the diagonal reference line of a random classifier, as the Notes ask, running from corner to corner, told apart from the model curves at a glance and visible in both themes.
- A good version shows: the AUC score in the legend or an annotation, as the Notes ask, placed so that it is clear which curve it belongs to.
- A good version shows: both axes spanning the full range of the rates, as the Notes ask, on a square plot area when the equal aspect ratio the Notes prefer is used, so the diagonal runs at the same slope as it does in the data.
- A good version shows: when several models are compared, each curve in its own color or line style, as the Notes ask, and named in a legend or by a direct label.
- Expected, not a defect: a stair-step curve from a finite sample, a curve that hugs the top-left corner for a strong model, curves that cross each other, and a stretch that dips below the diagonal.
