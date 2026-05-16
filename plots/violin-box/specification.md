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
