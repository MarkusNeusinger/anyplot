# circlepacking-basic: Circle Packing Chart

## Description

A circle packing chart displays hierarchical data as nested circles, where each circle contains smaller circles representing its children. Circle size is proportional to node value, and circles are packed efficiently without overlap. This visualization excels at revealing hierarchical structures while simultaneously showing quantitative relationships through area encoding.

## Applications

- File and folder size visualization showing directory hierarchy and storage consumption
- Organizational structure display with team sizes proportional to headcount or budget
- Portfolio composition analysis breaking down investments by asset class and holdings
- Taxonomy or classification hierarchies with proportional representation of categories

## Data

- `id` (string) - unique identifier for each node
- `parent` (string) - parent node identifier (null for root)
- `value` (numeric) - size value determining circle area (for leaf nodes)
- `label` (string) - display name for the node
- Size: 20-200 nodes across 2-4 hierarchy levels

## Notes

- Pack circles efficiently using force simulation or specialized packing algorithms
- Color by depth level or category to distinguish hierarchy levels
- Display labels for larger circles; smaller circles may show labels on hover
- Scale circle sizes by area (not radius) for accurate visual perception
- Root circle should encompass all children with appropriate padding

## What a good version looks like

- A good version shows: leaf circles whose area, not radius, is proportional to their value, as the Notes ask, so a value twice as large has twice the area.
- A good version shows: every circle fully inside its parent and the root circle enclosing all of them with some padding, as the Notes ask, with sibling circles packed closely and none crossing another or its parent's edge.
- A good version shows: color by depth level or by category, as the Notes ask, with each nesting level distinguishable from the one it sits in, by fill or outline, in both themes.
- A good version shows: labels for the larger circles, as the Notes ask, readable against their fill in both themes and not hidden behind the circles nested inside the one they name.
- A good version shows: the basic variant's nested circles, besides the labels the Notes ask for: position comes from the packing, not from data, so no axes or grid, and no color scale for a second variable, reference lines, highlighted circles or callouts.
- Expected, not a defect: empty space between circles and inside parents, parent circles larger than the sum of their children's areas, and small unlabeled leaves; only leaf areas are comparable.
