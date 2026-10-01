# radar-innovation-timeline: Innovation Radar with Time-Horizon Rings

## Description

A radial chart that maps innovations, technologies, or trends onto concentric rings representing time horizons and angular sectors representing thematic categories. Inner rings represent near-term items (e.g., "Now", "Next 6 months") while outer rings represent longer-term or emerging trends (e.g., "2-5 years", "Future"). Each item is placed as a labeled point within its sector and ring, with distinct markers or colors encoding categories. Inspired by ThoughtWorks Technology Radar and similar strategic planning visualizations.

## Applications

- Strategic technology planning: mapping emerging technologies by expected adoption timeline across domains like AI, cloud, and security
- Corporate innovation management: visualizing an R&D pipeline by expected market readiness and business unit
- Trend analysis: positioning industry trends from immediate to long-term horizon for executive briefings
- Investment planning: categorizing portfolio opportunities by time-to-market and sector

## Data

- `name` (string) - innovation or technology label displayed on the chart
- `ring` (categorical/ordinal) - time horizon ring assignment (e.g., "Adopt", "Trial", "Assess", "Hold" or "Now", "Near-term", "Mid-term", "Future")
- `sector` (categorical) - thematic category or quadrant (e.g., "AI & ML", "Sustainability", "Biotech", "Infrastructure")
- `x_angle` (numeric, optional) - angular position within sector for fine-grained placement control
- Size: 15-40 labeled items across 3-4 rings and 3-5 sectors

## Notes

- Use a half-circle (180 degrees) or three-quarter (270 degrees) layout to leave room for a legend or title area
- Draw concentric rings with clear boundary lines and label each ring with its time-horizon name
- Divide the angular space into equal sectors with labeled sector headers along the outer edge
- Use distinct marker shapes or colors per sector/category for visual grouping
- Labels must be readable and avoid overlapping — use smart label placement, slight angular jittering, or radial offset within rings
- Color-code points by sector/category and include a legend mapping colors/markers to categories
- Consider adding a subtle background fill per ring to visually separate time horizons

## What a good version looks like

- A good version shows: a half-circle or three-quarter-circle layout, as the Notes ask, with the open part of the circle left for the legend or title.
- A good version shows: concentric rings with clear boundary lines, each labeled with its time-horizon name, as the Notes ask, the nearest horizon innermost and later ones further out; a background fill per ring, if drawn as the Notes suggest, stays subtle.
- A good version shows: the angular space divided into equal sectors, each with a header along the outer edge, and the items color-coded by sector, with marker shapes if used, and a legend mapping them to the categories, as the Notes ask.
- A good version shows: every item as a marker inside the cell of its own ring and sector; where it sits inside that cell is layout, not data, unless an angle is given, so items may be spread apart but never across a ring or sector boundary.
- A good version shows: every item's name beside its marker, readable in both themes and kept apart from other labels, ring names and sector headers, as the Notes require.
- Expected, not a defect: cells with many items next to empty ones, items at irregular angles and depths inside a cell, and inner cells that look fuller than outer ones because they have less room.
