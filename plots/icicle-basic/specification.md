# icicle-basic: Basic Icicle Chart

## Description

An icicle chart displaying hierarchical data as adjacent rectangles in a layered structure, where each rectangle's size represents its value in the hierarchy. Unlike treemaps that nest rectangles, icicle charts stack them in rows (horizontal) or columns (vertical), making parent-child relationships explicitly visible through spatial adjacency. This layout excels at showing both the hierarchy levels and the proportional values simultaneously.

## Applications

- File system visualization showing directory structure and file sizes
- Organizational hierarchy displaying departments and team headcounts
- Budget breakdown by department, project, and expense category
- Website navigation structure with page hierarchy and traffic volume

## Data

- `name` (string) - node label for each element in the hierarchy
- `parent` (string) - parent node reference establishing the tree structure
- `value` (numeric) - size/magnitude determining each rectangle's width or height
- Size: 10-100 nodes recommended
- Example: File system with nested folders and file sizes

## Notes

- Use horizontal orientation (top-to-bottom) for deep hierarchies
- Color by hierarchy level or category for visual grouping
- Label rectangles that have sufficient space; hide labels for small nodes
- Root node at top/left with children below/right

## What a good version looks like

- A good version shows: one row per hierarchy level with the root at the top, or one column per level with the root at the left, and every node's children directly below or to the right of it, as the Notes ask.
- A good version shows: each rectangle's width, or its height in the column layout, proportional to its value, with children lying within their parent's extent and siblings adjacent, separated by thin borders at most.
- A good version shows: color by hierarchy level or by category, as the Notes ask, applied the same way across the whole chart, with neighboring rectangles distinguishable in both themes.
- A good version shows: labels in the rectangles that have room for them and none on small nodes, as the Notes ask, each inside its own rectangle and readable against its fill in both themes.
- A good version shows: the basic variant's rectangles, besides the labels the Notes ask for: position comes from the hierarchy layout, not from data, so no value axis or grid, and no color scale for a second variable, reference lines, highlighted nodes or paths, or callouts.
- Expected, not a defect: a root that spans the whole first row or column as one block, thin unlabeled slivers, and empty space beneath branches that end at a shallower level than others.
