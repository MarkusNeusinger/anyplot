# donut-basic: Basic Donut Chart

## Description

A donut chart (ring chart) showing proportions of categorical data as segments of a ring, with a hollow center. Similar to pie charts but the empty center can display summary statistics or additional information. The ring format can be easier to read when comparing segment sizes.

## Applications

- Budget allocation by category with total in center
- Market share distribution with company logo in center
- Progress tracking (completion percentage)
- Portfolio allocation by asset class

## Data

- `category` (string) - category labels
- `value` (numeric) - values for each category
- Size: 3-8 categories
- Example: Categorical data with proportional values (e.g., budget allocation by department, market share by company)

## Notes

- Use the center space for key metric or label
- Include percentage labels on segments
- Maintain consistent segment ordering
- Consider thick ring width for readability

## What a good version looks like

- A good version shows: one segment per category in a round, undistorted ring around a hollow center, each segment's arc proportional to its value and the segments together closing the full ring; position is angle, not data, so there are no axes or grid.
- A good version shows: the center space holding a key metric or label, as the Notes ask, such as the total, readable in both themes and clear of the ring.
- A good version shows: a percentage label for every segment, as the Notes ask, matching the segment's share, on the segment or beside it with a leader line where the segment is narrow, readable in both themes and not colliding with other labels.
- A good version shows: one distinct color per segment, each segment named by its label or in a legend, and the segments in one consistent order around the ring, as the Notes ask, such as by size or the categories' natural order.
- A good version shows: the basic variant's single ring: besides the center metric or label the Notes ask for, no second ring, exploded or otherwise highlighted segments, highlight bands, reference lines, or callouts beyond the segment labels.
- Expected, not a defect: segments of very different size, including one dominant segment and a thin sliver whose label sits outside the ring, and a ring that is thick, as the Notes suggest, with only a small hole.
