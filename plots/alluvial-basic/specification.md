# alluvial-basic: Basic Alluvial Diagram

## Description

An alluvial diagram visualizes how entities flow or transition between discrete categories across multiple time points or ordered stages. Unlike general Sankey diagrams, alluvial diagrams enforce strict vertical ordering where each column represents a specific time step or category dimension. Bands connect related segments to show how proportions shift over time, making it ideal for tracking structural changes, migrations, and transitions in categorical data.

## Applications

- Tracking voter migration between political parties across multiple election cycles
- Visualizing customer journey stages from acquisition through retention or churn
- Showing how students transition between academic tracks or performance categories over semesters

## Data

- `time_point` (categorical/ordinal) - discrete time steps or ordered stages (columns)
- `category` (categorical) - the category or state at each time point
- `value` (numeric) - count or proportion of entities in each category at each time point
- `flow` (numeric) - magnitude of transition between categories across time points
- Size: 3-6 time points, 3-8 categories per time point
- Example: Election data with years as time points, parties as categories, and voter counts as values

## Notes

- Time points should be arranged left-to-right in chronological or logical order
- Use consistent colors for categories that persist across time points
- Band width should be proportional to flow magnitude
- Consider using transparency for overlapping flows to improve readability
- Labels should clearly identify both time points (column headers) and categories (node labels)

## What a good version looks like

- A good version shows: one column per time point, in chronological or logical order from left to right, as the Notes ask, each column a stack of category blocks whose heights are the categories' values at that time point.
- A good version shows: bands between neighboring columns only, each with a width proportional to its flow, as the Notes ask, and attached to the blocks of the categories it leaves and enters; the vertical order of blocks and bands is a layout choice, and only heights and widths carry values.
- A good version shows: each category in the same color at every time point, as the Notes ask, with bands tied by color to a category they connect; the transparency the Notes suggest, if used, keeps overlapping bands distinguishable in both themes.
- A good version shows: every time point named in a column header and the categories named by labels at their blocks, with or without the block's value, as the Notes ask.
- A good version shows: the basic variant's single alluvial diagram: besides the blocks, bands, column headers and category labels, no highlighted bands or blocks, emphasis that separates stable from changed flows, reference lines, callouts or trend annotations, or second panel.
- Expected, not a defect: bands that cross, blended color where translucent bands overlap, hair-thin bands for rare transitions, and blocks of unequal height that grow or shrink from one column to the next.
