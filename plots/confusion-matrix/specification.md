# confusion-matrix: Confusion Matrix Heatmap

## Description

A specialized heatmap visualization for evaluating classification model performance, displaying the counts or proportions of predicted vs actual class labels. The confusion matrix reveals true positives, false positives, true negatives, and false negatives at a glance, making it essential for understanding model behavior, identifying class imbalances, and diagnosing specific misclassification patterns.

## Applications

- Binary classification model evaluation showing sensitivity and specificity
- Multi-class classifier performance analysis with per-class accuracy breakdown
- Model comparison to identify which classes are most often confused
- Error analysis to understand systematic misclassification patterns

## Data

- `true_labels` (categorical) - ground truth class labels for each sample
- `predicted_labels` (categorical) - model-predicted class labels for each sample
- `class_names` (string) - display names for each class on the axes
- Size: 2-20 classes (larger matrices may have readability issues)
- Example: Classification results from a trained model on test data

## Notes

- Label axes clearly: "True Label" (y-axis) and "Predicted Label" (x-axis)
- Annotate cells with counts or percentages for precise interpretation
- Support normalization options: none (raw counts), by row (recall), by column (precision), or by total
- Use sequential colormap (e.g., Blues) for count data
- Include colorbar showing the value scale
- Consider highlighting diagonal (correct predictions) for visual clarity

## What a good version looks like

- A good version shows: a square grid with the true labels on the y axis and the predicted labels on the x axis, as the Notes ask, the same class names in the same order on both axes, so the correct predictions fall on one diagonal.
- A good version shows: every cell annotated with its count or percentage, as the Notes ask, legible against light and dark cells alike in both themes.
- A good version shows: a sequential colormap and a color bar showing the value scale, as the Notes ask, with color intensity rising with the cell value, so the strongest cells stand out in both themes.
- A good version shows: values that say what they are: raw counts, or proportions under one of the normalizations the Notes list, with the color bar or a label naming which.
- A good version shows: the diagonal highlight the Notes allow, if drawn, as an outline or emphasis that leaves the cell colors and numbers readable.
- Expected, not a defect: off-diagonal cells at or near zero that look empty, a diagonal that takes up most of the color range, diagonal cells of unequal depth when classes are imbalanced, and a matrix that is not symmetric.
