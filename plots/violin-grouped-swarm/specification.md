# violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay

## Description

A grouped violin plot with individual data points overlaid as swarm points, showing distributions across two categorical dimensions simultaneously. Multiple violin plots are arranged by category on the x-axis and grouped by a secondary variable using color/hue, with swarm points revealing the underlying raw data. This visualization combines distribution shape visualization with complete data transparency, ideal for comparing how distributions differ across multiple factors.

## Applications

- Comparing drug efficacy distributions across multiple dosage levels and treatment groups
- Analyzing performance metrics across departments and employee seniority levels
- Visualizing experimental results across conditions and time points in research studies
- Comparing customer satisfaction scores across product categories and regions

## Data

- `category` (categorical) - Primary grouping variable for x-axis positioning
- `group` (categorical) - Secondary grouping variable for hue/color differentiation
- `value` (numeric) - Continuous variable values shown on the value axis
- Size: 20-150 observations per category-group combination, 2-4 categories, 2-4 groups
- Example: Response times across 3 task types and 2 expertise levels with 40 observations each

## Notes

- Use distinct colors for each group with a clear legend
- Apply transparency to violins (alpha 0.4-0.6) so swarm points remain visible
- Size swarm points appropriately (smaller than single-category version due to space constraints)
- Ensure adequate spacing between grouped violins to prevent overlap
- Swarm points should match the hue of their corresponding violin
- Consider dodging swarm points to align with their respective violin position

## What a good version looks like

- A good version shows: within each category, one mirrored violin per group placed side by side, with enough space that neighboring violins do not run into each other, as the Notes ask.
- A good version shows: each group in its own distinct color, the same in every category, and a legend naming each group, as the Notes ask.
- A good version shows: translucent violin fills, as the Notes ask, so the swarm points drawn over them stay visible in both themes.
- A good version shows: swarm points in the hue of their own violin, as the Notes ask, of one size and small enough to fit the narrow grouped violins.
- A good version shows: every swarm point at its value on the value axis, spread only across the category direction, and, where dodged as the Notes suggest, centered on its own group's violin.
- Expected, not a defect: sideways swarm offsets, which are layout rather than data, points packed edge to edge in the densest value range, violins of different width and length, multimodal or skewed shapes, and groups whose value ranges overlap.
