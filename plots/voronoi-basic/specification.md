# voronoi-basic: Voronoi Diagram for Spatial Partitioning

## Description

A Voronoi diagram partitions a plane into regions based on the distance to a set of seed points, where each region contains all points closer to its seed than to any other. This visualization is essential for understanding spatial relationships, proximity analysis, and territorial boundaries. It reveals natural clustering patterns and helps identify areas of influence around data points.

## Applications

- Analyzing service area coverage for retail stores or emergency facilities based on customer proximity
- Visualizing territorial boundaries in ecological studies to show animal home ranges or plant distribution zones
- Mapping nearest-neighbor relationships in urban planning for optimizing resource placement like cell towers or hospitals

## Data

- `x` (float) - X-coordinate of seed points
- `y` (float) - Y-coordinate of seed points
- `label` (string, optional) - Identifier for each seed point
- Size: 10-50 seed points recommended for clear visualization
- Example: Random or structured point distribution within a bounded region

## Notes

- Cells should be clipped to a visible bounding box to prevent infinite regions
- Each Voronoi cell should be visually distinguishable through colors or edge styling
- Seed points should be clearly marked within their respective cells
- Consider using a color palette that allows easy differentiation of adjacent regions

## What a good version looks like

- A good version shows: one cell per seed, holding that seed and every location closer to it than to any other seed, so the cells tile the visible bounding box without gaps or overlaps and the outer cells are clipped at the box, as the Notes ask.
- A good version shows: straight cell edges, each lying midway between the two seeds it separates and at right angles to the line joining them, so every cell is a convex polygon.
- A good version shows: every seed marked at its exact x and y coordinates inside its own cell, as the Notes ask, never moved to the cell's center, standing out from every fill in both themes, with seed labels, if drawn, next to their seed.
- A good version shows: cells told apart by fill colors or edge styling, as the Notes ask, with the boundaries visible in both themes; where fills alone carry the distinction, cells that share an edge differ in color.
- Expected, not a defect: cells of very unequal size and shape, small crowded cells where seeds cluster, large elongated border cells cut by the bounding box, and seeds that sit far off-center in their cells; cell shapes follow from the seeds, not from a layout choice.
- A good version shows: the basic variant's single partition: besides the seed points and the seed labels the Data allows, no triangulation or other overlay, reference or mean lines, highlighted cells or seeds, callouts, or fill colors that encode a second variable.
