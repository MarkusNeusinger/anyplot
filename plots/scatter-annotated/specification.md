# scatter-annotated: Annotated Scatter Plot with Text Labels

## Description

A scatter plot where each data point can have a text label annotation, useful for identifying specific points of interest. This visualization enhances basic scatter plots by adding contextual information directly on the chart, making it easy to highlight outliers, named entities, or key data points that deserve special attention.

## Applications

- Labeling company names on a market cap vs. revenue scatter plot
- Identifying outlier cities in a population vs. area analysis
- Annotating key experiments in a scientific study comparing two measurements
- Highlighting top performers in a sales vs. customer satisfaction comparison

## Data

- `x` (numeric) - Independent variable values plotted on the horizontal axis
- `y` (numeric) - Dependent variable values plotted on the vertical axis
- `label` (string) - Text annotation to display near each point
- Size: 10-50 points recommended to avoid label overlap and maintain readability
- Example: Named data points with random coordinates demonstrating typical annotation patterns

## Notes

- Use adjustText or similar libraries to avoid overlapping labels where supported
- Consider annotating only a subset of important points for large datasets
- Text should be legible with appropriate font size and contrast
- Include subtle connecting lines or arrows from labels to points when offset
- Points should have moderate transparency (alpha ~0.7) to reveal any overlap

## What a good version looks like

- A good version shows: every point as a marker at its exact (x, y) value with its text label beside it; labels shift to make room for each other, the points never do.
- A good version shows: labels that collide neither with each other nor with the markers, as the Notes ask, each one close enough to its point, or tied to it by a thin leader line when offset, that the point it names is unambiguous.
- A good version shows: label text legible in both themes, in a size that fits the number of labels, with leader lines, if drawn, subtler than the markers and the text.
- A good version shows: translucent markers, as the Notes ask, so points that overlap can still be told apart under the labels.
- Expected, not a defect: labels on only a subset of the points when there are many, as the Notes allow, labels on different sides and at different distances from their points, and leader lines of unequal length.
