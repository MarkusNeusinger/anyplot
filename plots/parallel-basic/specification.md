# parallel-basic: Basic Parallel Coordinates Plot

## Description

A parallel coordinates plot visualizes multivariate data by representing each variable as a vertical axis and each observation as a line connecting values across all axes. This technique is powerful for identifying patterns, clusters, and outliers in high-dimensional datasets where traditional 2D plots fall short. It enables simultaneous comparison of multiple variables for each data point.

## Applications

- Comparing product features across multiple dimensions (price, rating, sales, inventory) to identify market segments
- Analyzing patient health metrics (blood pressure, heart rate, cholesterol, BMI) to detect health patterns or anomalies
- Evaluating machine learning model hyperparameters and their corresponding performance metrics to find optimal configurations

## Data

- `dimension_1` through `dimension_n` (numeric) - Multiple numeric variables for each observation
- `category` (categorical, optional) - Group identifier for color coding lines
- Size: 20-200 observations with 4-10 dimensions recommended
- Example: Iris dataset with sepal length, sepal width, petal length, petal width

## Notes

- Normalize or standardize variables to the same scale for fair comparison across axes
- Consider axis ordering to reveal correlations between adjacent variables
- Use transparency (alpha) to handle overlapping lines when many observations exist
- Color coding by category helps distinguish groups in the data

## What a good version looks like

- A good version shows: one vertical axis per variable, evenly spaced and named, and one polyline per observation crossing every axis at that observation's value, with straight segments between neighboring axes and no line smoothed or shifted off its values.
- A good version shows: variables brought to the same scale, as the Notes ask, so that lines spread along every axis instead of one variable's larger units squeezing the others flat.
- A good version shows: transparency on the lines when there are many observations, as the Notes ask, so that bundles of similar observations read darker than single lines.
- A good version shows: the basic variant's plain polylines across parallel axes, with the color by category the Notes allow and its legend: no reference or mean lines, highlighted lines or bands, callouts, curved or bundled lines, or histograms and box plots on the axes.
- Expected, not a defect: many lines crossing and overlapping, a tangle of crossings between two neighboring axes whose variables run opposite to each other, single lines straying from their bundle, and original units that cannot be read from normalized axes.
