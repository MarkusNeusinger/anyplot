# box-horizontal: Horizontal Box Plot

## Description

A horizontal box plot displays the distribution of numerical data through quartiles with the boxes oriented horizontally. This orientation is particularly useful when category labels are long or when comparing many groups, as it allows for easier reading of labels on the y-axis.

## Applications

- Comparing distributions across many categories with long names
- Displaying salary ranges by job title or department
- Analyzing test score distributions by course or subject
- Visualizing response time distributions by service type

## Data

- `categories` (categorical) - Groups or categories for comparison (displayed on y-axis)
- `values` (numeric) - Numeric values to show distribution (displayed on x-axis)
- Size: 10–100 points (varies by number of groups and observations per group)
- Example: Salary ranges by job title, test score distributions by course

## Notes

- Same statistical elements as vertical box plot: median line, quartile box, whiskers, outliers
- Particularly effective when category names are long
- Consider sorting categories by median value for easier comparison
- Whiskers typically extend to 1.5 * IQR

## What a good version looks like

- A good version shows: boxes running horizontally, with the categories on the y axis and the values on the x axis, so each category name reads horizontally beside its own box.
- A good version shows: each box spanning the first to the third quartile along the value axis, with a median line visible against the box fill in both themes, whiskers on both sides, and any value beyond the whiskers as an individual point at its value.
- A good version shows: one shared value axis for all boxes that is not forced to zero, so medians and spreads compare directly along it.
- A good version shows: categories in a readable order: sorted by median value, as the Notes suggest, or kept in their natural, original or alphabetical order.
- Expected, not a defect: outlier points beyond the whiskers, boxes without any, boxes of very different length, a median that sits off-center in its box and whiskers of unequal length; they are the point of the chart, not an imbalance to fix.
