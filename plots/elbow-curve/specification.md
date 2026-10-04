# elbow-curve: Elbow Curve for K-Means Clustering

## Description

An elbow curve visualizes the relationship between the number of clusters (k) and within-cluster sum of squares (inertia/distortion) in K-means clustering. The plot helps identify the optimal number of clusters by finding the "elbow point" where adding more clusters yields diminishing returns in reducing inertia. This is a fundamental diagnostic tool for unsupervised learning parameter selection.

## Applications

- Selecting the optimal number of clusters (k) in K-means clustering analysis
- Customer segmentation to determine natural groupings in behavioral data
- Image compression parameter selection for color quantization
- Document clustering to identify topic groupings in text corpora

## Data

- `k_values` (numeric) - Number of clusters tested (typically 1 to 10 or 15)
- `inertia` (numeric) - Within-cluster sum of squares for each k value
- Size: 8-15 different k values for clear elbow visualization
- Example: Scikit-learn's `KMeans.inertia_` attribute across multiple k values

## Notes

- X-axis shows number of clusters (k), y-axis shows inertia/distortion
- The elbow point is where the rate of decrease sharply changes
- Consider annotating or highlighting the optimal k value
- Use markers at each data point to show discrete k values tested
- A line joins the markers in k order, passing through every computed value (straight or monotone-interpolated segments; no fitted smoothing)

## What a good version looks like

- A good version shows: inertia on the y axis against the number of clusters on the x axis, with a marker at every tested k, as the Notes ask, at its own inertia value, and a line joining the markers in order of k.
- A good version shows: an x axis whose ticks fall on whole numbers of clusters, because k is a count.
- A good version shows: a curve that falls as k grows, steeply at first and then gently, with the bend between the two parts visible at the plot's proportions.
- A good version shows: the optimal k, if annotated or highlighted, marked at the curve's own point for that k, by a marker, a vertical line or a label that names the value.
- Expected, not a defect: an elbow that is a soft bend and not a sharp corner, inertia still falling slowly after the elbow, without reaching zero, and a first drop that dwarfs all later ones.
