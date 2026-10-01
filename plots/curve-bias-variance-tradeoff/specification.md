# curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve

## Description

A theoretical visualization of the bias-variance tradeoff showing how total prediction error decomposes into bias squared, variance, and irreducible noise as a function of model complexity. The plot displays multiple curves: bias squared (decreasing with complexity), variance (increasing with complexity), irreducible error (constant), and total error (U-shaped). This is one of the most fundamental conceptual plots in machine learning for understanding model selection, overfitting, and underfitting.

## Applications

- ML education: explaining the fundamental tradeoff between underfitting (high bias) and overfitting (high variance)
- Model selection: visualizing why more complex models are not always better
- Regularization justification: understanding why adding constraints to models improves generalization
- Algorithm comparison: explaining why ensemble methods work by reducing variance

## Data

- `model_complexity` (numeric) - x-axis representing model flexibility (e.g., polynomial degree, tree depth, number of parameters)
- Theoretical curves (generated, not empirical data):
  - `bias_squared` (numeric) - decreasing function of complexity (e.g., 1/(1 + complexity))
  - `variance` (numeric) - increasing function of complexity (e.g., complexity/scale)
  - `irreducible_error` (numeric) - constant horizontal line representing noise floor
  - `total_error` (numeric) - sum of bias_squared + variance + irreducible_error
- Size: 50-100 points for smooth curves

## Notes

- X-axis: Model Complexity (labeled from "Low" to "High" or with specific values)
- Y-axis: Prediction Error
- Display 4 curves with distinct colors and line styles: Bias squared, Variance, Total Error, Irreducible Error
- Mark the optimal complexity point where total error is minimized with a vertical line or annotation
- Use annotations to label each curve directly on the plot
- Include the formula: Total Error = Bias² + Variance + Irreducible Error
- Consider adding shaded regions to indicate underfitting zone (left) and overfitting zone (right)

## What a good version looks like

- A good version shows: four curves over model complexity: bias squared falling, variance rising, the irreducible error as a flat horizontal line, and the total error as a U-shaped curve that lies above the other three as their sum.
- A good version shows: the four curves in distinct colors and line styles, each labeled by an annotation directly on the plot, as the Notes ask, with every label next to its own curve.
- A good version shows: the optimal complexity marked with a vertical line or an annotation, as the Notes ask, exactly at the minimum of the total error curve.
- A good version shows: the formula that decomposes the total error into bias squared, variance and irreducible error written on the plot, as the Notes ask, legible and clear of the curves.
- A good version shows: shaded underfitting and overfitting zones, if drawn, to the left and right of the optimum, labeled and light enough that the curves stay dominant in both themes.
- Expected, not a defect: perfectly smooth curves without noise, because the plot is theoretical, a complexity axis that reads only from Low to High without numeric ticks, and bias and variance curves that cross at a point other than the optimum.
