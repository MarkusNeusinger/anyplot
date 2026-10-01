# subplot-grid: Subplot Grid Layout

## Description

A customizable grid of multiple subplots allowing different plot types in each cell, with shared or independent axes. Unlike faceted plots that repeat the same visualization for data subsets, subplot grids enable combining distinct visualizations (scatter, line, bar, histogram, etc.) into a cohesive multi-panel figure for comprehensive data presentation.

## Applications

- Dashboard-style visualizations combining multiple metrics in a single figure
- Scientific publications requiring related but distinct plots side-by-side
- Exploratory data analysis comparing different visualization approaches
- Technical reports showing complementary views of the same dataset

## Data

- `x` (numeric or categorical) - Primary variable for each subplot
- `y` (numeric) - Secondary variable for each subplot
- Size: Varies per subplot, typically 20-200 points per cell
- Example: Financial dashboard with price line chart, volume bars, and returns histogram

## Notes

- Grid dimensions should be configurable (e.g., 2x2, 2x3, 3x1)
- Support both shared axes (for comparison) and independent axes (for different scales)
- Each cell can contain a different plot type
- Consistent spacing and alignment across all subplots
- Clear titles or labels for each subplot to identify its content

## What a good version looks like

- A good version shows: several subplots in one regular grid of rows and columns, each cell a complete plot of its own with its marks at their data values, and the cells together reading as related views of one scenario.
- A good version shows: consistent spacing and alignment across all subplots, as the Notes ask: plot areas line up along the rows and columns, the gaps between them are even, and no subplot's tick labels, axis titles or legend run into a neighbor.
- A good version shows: a title or label on each subplot that identifies its content, as the Notes ask, readable in both themes.
- A good version shows: shared axes, if used, visibly on one scale and range across the subplots they link; independent axes each with their own tick labels and axis title, so every such subplot can be read alone.
- A good version shows: a legend or color bar that belongs to one subplot placed inside or directly beside that subplot, so it is clear which cell it explains.
- Expected, not a defect: different plot types, units, value ranges and amounts of data from cell to cell, axis titles repeated on subplots with independent axes, tick labels omitted on the inner edges of shared axes, and no legend for the figure as a whole.
