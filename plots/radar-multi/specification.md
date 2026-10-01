# radar-multi: Multi-Series Radar Chart

## Description

A multi-series radar chart overlays multiple data polygons on shared axes radiating from a center point, enabling direct comparison across several entities or categories. Each series is rendered as a distinct colored polygon, making it easy to identify relative strengths and weaknesses at a glance. This visualization excels at comparative analysis where multiple subjects are evaluated across the same set of metrics.

## Applications

- Product feature comparison showing how competing products score across attributes like price, quality, durability, and support
- Employee or team skill assessments comparing individuals across competencies such as communication, technical skills, leadership, and creativity
- Sports player or team performance comparison across metrics like speed, accuracy, endurance, and teamwork
- Business competitor analysis across key performance indicators such as market share, customer satisfaction, and innovation

## Data

- `category` (string) - axis labels representing different variables/dimensions being compared
- `value` (numeric) - values for each axis per series (0-100 scale recommended for clarity)
- `series` (string) - identifier for each data series (e.g., product name, person name, team)
- Size: 5-8 axes, 2-5 series for optimal comparison clarity

## Notes

- Use filled polygons with transparency (alpha ~0.2-0.3) to allow visibility of overlapping areas
- Assign distinct, contrasting colors to each series for easy differentiation
- Include a legend identifying each series by color
- Add gridlines at regular intervals (e.g., 20, 40, 60, 80, 100) for value reference
- Label each axis clearly at the outer edge
- Close each polygon by connecting the last point back to the first
- Consider using both fill and outline for each polygon to enhance visibility

## What a good version looks like

- A good version shows: one axis spoke per variable, the spokes evenly spaced around a common center and shared by all series on one value scale, each labeled at its outer end, as the Notes ask.
- A good version shows: one polygon per series, its vertices on the spokes at that series' values, closed by joining the last point back to the first, as the Notes ask, and never smoothed past its vertices.
- A good version shows: translucent fills, as the Notes ask, so that every polygon and the gridlines stay visible where polygons overlap; an outline, if drawn as the Notes suggest, follows the same vertices in the series' color.
- A good version shows: a distinct, contrasting color per series, distinguishable in both themes, and a legend naming each series by its color, as the Notes ask.
- A good version shows: gridlines at regular value intervals, as the Notes ask, drawn as rings or polygons with their values labeled and lighter than the data.
- Expected, not a defect: overlapping polygons and crossing outlines, vertices that nearly coincide where series score alike, a polygon lying wholly inside another, and shapes and enclosed areas that depend on the order of the axes.
