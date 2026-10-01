# polar-line: Polar Line Plot

## Description

A line plot rendered in polar coordinates, where data points are connected with lines around a circular axis. The angle (theta) typically represents a cyclical variable while the radius shows magnitude.

## Applications

- Cyclical data visualization (hours, months, seasons)
- Directional data with continuous measurements
- Periodic pattern analysis
- Angular velocity or rotation data

## Data

- `theta` (numeric) - Angular position in degrees or radians (e.g., 0-360 or 0-2π)
- `radius` (numeric) - Magnitude or distance from center; can represent any continuous measure
- Size: 20-500 points recommended
- Example: Daily measurements (24 hours × multiple days) or seasonal patterns (12 months × multiple years)

## Notes

- Line connects points in theta order
- Can show multiple series with different colors
- Often used for time-of-day or seasonal patterns
- Grid lines are concentric circles and radial lines

## What a good version looks like

- A good version shows: each series as one line joining its points in theta order, as the Notes say, every point at its own angle and radius and the line never smoothed past the points it connects.
- A good version shows: markers, if drawn, sitting exactly on the line at the data values and small enough that the line still reads as a line.
- A good version shows: a grid of concentric circles and radial lines, as the Notes describe, lighter than the data lines and visible in both themes, with the angles and the radius values labeled.
- A good version shows: several series, if drawn as the Notes allow, in different colors named in a legend, all on the same angular and radial scales.
- Expected, not a defect: a line closed into a loop for cyclic data, and an open line or one that winds around more than once otherwise, loops that cross each other, a series with small values drawn as a small loop near the center beside a much larger one, and lopsided shapes.
