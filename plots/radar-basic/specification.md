# radar-basic: Basic Radar Chart

## Description

A radar chart (also known as spider or web chart) displays multivariate data on axes starting from a common center point, with values connected to form a polygon. Each axis represents a different variable, making it ideal for comparing multiple quantitative variables at once or visualizing strengths and weaknesses across categories.

## Applications

- Employee performance reviews showing scores across multiple competencies (communication, technical skills, teamwork, etc.)
- Product feature comparisons across attributes like price, quality, durability, and ease of use
- Sports player statistics comparing metrics such as speed, strength, accuracy, and stamina
- Company benchmarking across key performance indicators

## Data

- `category` (string) - axis labels representing different variables/dimensions
- `value` (numeric) - values for each axis (0-100 scale recommended for clarity)
- Size: 4-8 axes, 1-3 series for comparison

## Notes

- Use filled polygons with transparency (alpha ~0.25) for overlap visibility when comparing multiple series
- Include gridlines at regular intervals (e.g., 20, 40, 60, 80, 100)
- Label each axis clearly at the outer edge
- Use distinct colors for multiple series with a legend
- Close the polygon by connecting the last point back to the first

## What a good version looks like

- A good version shows: one axis spoke per variable, the spokes evenly spaced around a common center and sharing one value scale from the center outward, each labeled at its outer end, as the Notes ask.
- A good version shows: each series as a polygon whose vertices lie on the spokes at their values, closed by joining the last point back to the first, as the Notes ask, and never smoothed past its vertices.
- A good version shows: gridlines at regular value intervals, as the Notes ask, drawn as rings or polygons with their values labeled, lighter than the data and visible in both themes.
- A good version shows: where several series are compared, translucent fills that keep every polygon visible through the others, a distinct color per series and a legend, as the Notes ask.
- A good version shows: the basic variant's polygons for the series the Data allows: besides the axis spokes and gridlines, no reference or mean lines, rings or polygons, highlighted axis, sector or band, callouts on gaps or extremes, or second panel.
- Expected, not a defect: polygons that overlap or nearly coincide on some axes, irregular and spiky outlines, and a shape and enclosed area that depend on the order of the axes.
