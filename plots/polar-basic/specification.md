# polar-basic: Basic Polar Chart

## Description

A polar chart displays data points on a circular coordinate system where position is determined by angle (theta) and distance from center (radius). This visualization is ideal for cyclical patterns, directional data, or any dataset where angular relationships are meaningful. It reveals periodic trends and directional distributions that would be obscured in Cartesian coordinates.

## Applications

- Displaying wind speed and direction measurements from weather stations
- Visualizing time-of-day patterns (e.g., website traffic by hour, energy consumption cycles)
- Showing compass-based data such as animal migration directions or survey response distributions
- Analyzing seasonal patterns where the circular nature emphasizes yearly cycles

## Data

- `theta` (numeric) - Angular position in degrees (0-360) or radians (0-2π)
- `radius` (numeric) - Distance from center, representing the measured value
- `category` (string, optional) - Labels or groups for data points
- Size: 12-100 points recommended for clarity
- Example: Hourly temperature readings, wind direction frequency, or activity levels by hour

## Notes

- Radial gridlines should be clearly visible but not overwhelming
- Angular labels should be at standard intervals (0°, 90°, 180°, 270° or compass directions)
- Consider starting angle at top (90°) for time-based data or at right (0°) for standard mathematical convention
- Use appropriate radial scale that doesn't compress data near the center

## What a good version looks like

- A good version shows: every observation at its own angle and radius on a circular axis, drawn as points, a connected line or wedges, and never moved or smoothed off its values.
- A good version shows: concentric radial gridlines that are visible in both themes yet lighter than the data, as the Notes ask, so a radius can be read against them.
- A good version shows: angular labels at standard, regular intervals around the circle, as the Notes ask (quarter turns in degrees, compass directions or the cycle's own units), with the starting angle where the data's convention puts it, such as the top for time-based data.
- A good version shows: a radial scale that spreads the data over the radius, as the Notes ask, so small values are not squeezed into the center.
- A good version shows: the basic variant's angle and radius only: one color for all marks, or the optional category the Data allows shown as groups or labels, and no reference or mean lines or rings, highlighted points, sectors or bands, callouts or annotations of extrema, or color scale.
- Expected, not a defect: marks that sit closer together near the center, where the same angular step covers less distance, stretches of the circle left empty when the data favors some directions, and a lopsided outline.
