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
