# ternary-basic: Basic Ternary Plot

## Description

A ternary plot displays three-component compositional data on an equilateral triangle where each vertex represents 100% of one component. Points inside the triangle show compositions that sum to a constant total (usually 100%), with position indicating relative proportions. This visualization is essential for data where three variables are interdependent and constrained to sum to a fixed value.

## Applications

- Analyzing chemical or material compositions (e.g., alloy mixtures, cement formulations)
- Soil classification using sand, silt, and clay proportions
- Visualizing market share distribution among three competitors
- Studying color mixing with RGB or other three-component systems

## Data

- `component_a` (numeric) - Proportion of first component (0-100%)
- `component_b` (numeric) - Proportion of second component (0-100%)
- `component_c` (numeric) - Proportion of third component (0-100%)
- Size: 20-200 points work well; larger datasets may need density visualization
- Constraint: All three components must sum to 100% (or a constant total)

## Notes

- Grid lines should be drawn at regular intervals (typically 10% or 20%)
- Each vertex should be clearly labeled with component names
- Points should be visually distinct with appropriate marker size and color
- Consider adding tick marks along each edge to aid reading proportions

## What a good version looks like

- A good version shows: an equilateral triangle with three equal-looking sides, each vertex labeled with the name of the component that is 100 percent there, as the Notes ask.
- A good version shows: every point at its true ternary position, its distance from each side proportional to the component of the opposite vertex, so compositions rich in one component sit near that vertex and no point is moved to separate it from its neighbors.
- A good version shows: grid lines at regular intervals for all three components, as the Notes ask, each set parallel to the side opposite its component's vertex, kept inside the triangle and lighter than the points.
- A good version shows: tick marks or tick labels along the edges, if drawn as the Notes suggest, in the same regular steps as the grid and placed so each edge's scale can be matched to one component and its direction of increase.
- A good version shows: the basic variant's single set of points in one color inside the gridded triangle, with the edge ticks the Notes allow: no color or size channel, no reference or mean lines, no highlighted points or shaded classification regions, no callouts or point labels, and no density shading or contours.
- Expected, not a defect: points overlapping where compositions cluster, a cloud confined to one part of the triangle with the rest empty, points on an edge or at a vertex when a component is zero, and no Cartesian x or y axes.
