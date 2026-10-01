# learning-curve-basic: Model Learning Curve

## Description

A learning curve visualizes model performance (training and validation scores) as a function of training set size. It is essential for diagnosing bias vs variance tradeoffs, determining whether collecting more data would improve model performance, and guiding model selection decisions. The plot typically shows two lines with shaded confidence bands representing variability across cross-validation folds.

## Applications

- Diagnosing underfitting (high bias) when both training and validation scores are low
- Diagnosing overfitting (high variance) when training score is high but validation score is low with a large gap
- Determining if collecting more training data would improve model performance
- Comparing learning characteristics across different model architectures

## Data

- `train_sizes` (numeric) - Array of training set sizes used for evaluation
- `train_scores` (numeric) - Training scores at each sample size (2D: folds × sizes)
- `validation_scores` (numeric) - Validation scores at each sample size (2D: folds × sizes)
- Size: 5-20 different training set sizes, typically with 5-10 cross-validation folds
- Example: Scikit-learn's `learning_curve` function output

## Notes

- Use shaded regions to show confidence bands (e.g., ±1 standard deviation across folds)
- Clearly label the y-axis with the metric being evaluated (accuracy, F1, MSE, etc.)
- Include a legend distinguishing training from validation curves
- X-axis should show actual sample sizes or percentages of total training data
- Consider using distinct colors (e.g., blue for training, orange for validation) for clarity

## What a good version looks like

- A good version shows: the training score and the validation score as two lines against training set size, each passing through its mean across folds at every evaluated size and not smoothed between them.
- A good version shows: a shaded band around each line for the variability across folds, as the Notes ask, translucent enough that the other curve and band stay visible where they overlap, in both themes.
- A good version shows: a legend that distinguishes the training curve from the validation curve, as the Notes ask, with the two told apart at a glance, by distinct colors if the Notes' suggestion is followed.
- A good version shows: the x axis in actual sample sizes or percentages of the training data and the y axis labeled with the metric being evaluated, as the Notes ask.
- A good version shows: the basic variant's single model and metric: the training and validation curves, their bands and the legend the Notes ask for, and no second model, no reference, target or mean lines, no highlighted regions or points, no callouts and no second panel.
- Expected, not a defect: a gap between the two curves, a training score that falls while the validation score rises, bands that are wider at small training sizes or overlap each other, and curves that have not converged at the largest size.
