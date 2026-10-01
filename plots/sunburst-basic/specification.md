# sunburst-basic: Basic Sunburst Chart

## Description

A sunburst chart displays hierarchical data as concentric rings, where each ring represents a level in the hierarchy. Inner rings show parent categories while outer rings show their children, with segment angles proportional to values. This radial visualization excels at revealing hierarchical structures and part-to-whole relationships across multiple levels simultaneously.

## Applications

- File system visualization showing directory sizes and nested folder structures
- Organizational budget breakdown by department, team, and project
- Taxonomy or classification hierarchies with proportional representation
- Website navigation paths showing user flow through page hierarchies

## Data

- `level_1` (string) - root/parent category (innermost ring)
- `level_2` (string) - child category (second ring)
- `level_3` (string) - optional grandchild category (outer ring)
- `value` (numeric) - size/magnitude determining segment angle
- Size: 10-50 leaf nodes across 2-4 hierarchy levels

## Notes

- Use consistent colors within each branch to show relationships
- Label major segments; smaller segments may show labels on hover/interaction
- Maintain clear visual separation between hierarchy levels
- Inner segments should visually encompass their children's angular span

## What a good version looks like

- A good version shows: one concentric ring per hierarchy level, the first level innermost, each ring visibly separated from the next as the Notes ask, and each segment's angle proportional to its value.
- A good version shows: every child segment inside its parent's angular span, so that an inner segment's arc covers the arcs of all its children, as the Notes ask.
- A good version shows: consistent colors within each branch, as the Notes ask: children carry their top-level category's hue, and neighboring segments stay distinguishable through shade or thin separators in both themes.
- A good version shows: labels on the major segments, as the Notes ask, each within its own segment and readable against its fill in both themes.
- A good version shows: the basic variant's rings, besides the segment labels the Notes ask for: position comes from the hierarchy layout, not from data, so no axes or grid, and no color scale for a second variable, reference lines, highlighted or pulled-out segments, or callouts.
- Expected, not a defect: thin unlabeled outer segments, segments of very different angle, and outer segments that look larger than inner ones of the same value because a ring's area grows with its radius; the angle carries the value.
