# andrews-curves: Andrews Curves for Multivariate Data

## Description

Andrews curves visualization transforms multivariate observations into smooth Fourier series curves. Each data point is represented as a continuous function where variable values become coefficients in a Fourier expansion, producing distinctive wave patterns. This technique enables visual comparison of multivariate patterns, cluster identification, and outlier detection—observations with similar values across variables produce similar curves, while outliers appear as distinctly different patterns.

## Applications

- Comparing iris flower species across sepal/petal measurements to visualize natural clustering in botanical data
- Detecting anomalous network traffic patterns by transforming connection metrics into curves and identifying outliers
- Analyzing wine quality factors (acidity, sugar, alcohol, pH) to reveal how different quality grades separate visually

## Data

- `variable_1` through `variable_n` (numeric) - Multiple numeric attributes for each observation
- `category` (categorical, optional) - Group identifier for color coding curves
- Size: 30-150 observations with 4-8 dimensions recommended
- Example: Iris dataset with sepal length, sepal width, petal length, petal width by species

## Notes

- Normalize variables to similar scales before transformation to prevent dominant variables
- Use transparency (alpha < 0.5) when plotting many curves to reveal density patterns
- Color by category to highlight cluster separation between groups
- The parameter t typically ranges from -π to π for the Fourier expansion

## What a good version looks like

- A good version shows: one smooth, continuous curve per observation, its Fourier series evaluated densely enough along the parameter t that no corners show, every curve at its computed values.
- A good version shows: the parameter t on the x axis over one full period, typically from -π to π as the Notes say, the same range for every curve.
- A good version shows: variables normalized to similar scales before the transformation, as the Notes ask, so the curves differ in shape and not only in a vertical offset set by one dominant variable.
- A good version shows: transparency when many curves are drawn, as the Notes ask, so that bundles of similar observations read as darker bands.
- A good version shows: curves colored by category where the data has one, as the Notes ask, with a legend naming the groups, so that groups read as separate bundles wherever their variables differ.
- Expected, not a defect: curves crossing and overlapping throughout, groups that merge over parts of the t range and separate only in others, single curves straying from their bundle, and a y axis whose values carry no unit.
