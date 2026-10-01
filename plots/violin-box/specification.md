# violin-box: Violin Plot with Embedded Box Plot

## Description

A violin plot with an embedded box plot inside, combining the distribution shape visualization (KDE) with traditional quartile statistics. Shows both the probability density and summary statistics in one plot.

## Applications

- Complete distribution visualization
- Combining density estimate with summary statistics
- Detailed group comparisons
- Statistical presentations requiring both views

## Data

- `value` (numeric) - Values to visualize the distribution
- `group` (categorical) - Groups or categories to compare
- Size: 50–1000 points recommended (10+ per group for meaningful visualizations)
- Example: Height measurements across 3+ demographic groups, or test scores by experimental condition

## Notes

- Box plot centered inside violin
- Shows median, quartiles (box), and whiskers
- KDE (violin) shape visible around the box
- Outliers can be shown as points

## What a good version looks like

- A good version shows: a mirrored density shape for each group with a box plot centered inside it on the violin's axis, as the Notes ask.
- A good version shows: a box narrow enough that the violin's shape stays visible around it on both sides, as the Notes ask, with the box and its whiskers standing out against the violin fill in both themes.
- A good version shows: inside every violin a box from the first to the third quartile, a median mark at the median and whiskers, with outliers, if shown as the Notes allow, as individual points at their values.
- A good version shows: one shared value axis for all violins that is not forced to zero, so their positions compare directly, with each violin's tails ending near its data range instead of trailing far beyond it.
- Expected, not a defect: widths and lengths that differ between groups, multimodal or skewed shapes, a box that sits off-center along its violin, violin tails that reach past the whisker ends, and outlier points beyond the whiskers.
