# donut-nested: Nested Donut Chart

## Description

A nested donut chart displays hierarchical data as multiple concentric rings, where each ring represents a level of the hierarchy. Inner rings show parent categories while outer rings show their subdivisions. This visualization effectively reveals part-to-whole relationships across multiple levels while maintaining the familiar donut format.

## Applications

- Budget allocation showing department totals (inner) and expense categories (outer)
- Market share by region (inner) and product lines within each region (outer)
- Organization structure showing divisions and their teams
- Revenue breakdown by business unit and customer segments

## Data

- `level_1` (string) - parent category labels (inner ring)
- `level_2` (string) - child category labels (outer ring)
- `value` (numeric) - values for the innermost level
- Size: 3-6 parent categories, 2-5 children each
- Hierarchy: values aggregate from outer rings to inner rings

## Notes

- Use consistent color families per parent category (same hue, varying lightness)
- Align child segments with parent segment boundaries for clarity
- Include labels on larger segments, use legend for smaller ones
- Consider adding spacing between rings for visual separation
- Limit to 2-3 hierarchy levels to maintain readability

## What a good version looks like

- A good version shows: one concentric ring per hierarchy level around an empty center, parents on the inner ring and their subdivisions on the ring outside it, each segment's angle proportional to its value and each ring closing the full circle.
- A good version shows: each parent's children spanning that parent's arc, their outer boundaries aligned with the parent's segment boundaries, as the Notes ask.
- A good version shows: one color family per parent category, as the Notes ask: children in the parent's hue at varying lightness, the lightest still distinguishable from the page and from its neighbors in both themes.
- A good version shows: labels on the larger segments and a legend for the ones too small to label, as the Notes ask, with each label on or beside its own segment and not colliding with another label.
- A good version shows: segment positions that come from the ring layout, not from data, so no axes or grid, and the spacing between rings the Notes allow, if drawn, even all the way around.
- Expected, not a defect: segments of very different angle, thin slices named only in the legend, and parents with different numbers of children; unequal shares are the point of the chart.
