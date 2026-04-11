# heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data

## Description

A heatmap wrapped around a circle where the angular axis represents a cyclic variable (e.g., hour of day, month) and the radial axis represents a second categorical or ordinal variable (e.g., day of week, year). Cell color encodes the measured value. This visualization reveals patterns in data with inherent cyclical structure that rectangular heatmaps distort, since the first and last angular bins are visually adjacent rather than separated at opposite ends of a row.

## Applications

- Showing website traffic intensity by hour of day (angular) and day of week (radial)
- Visualizing crime frequency by time of day and location zone
- Displaying energy consumption patterns by month (angular) and year (radial)
- Analyzing sensor data with daily or weekly cycles across multiple stations or categories

## Data

- `angular` (categorical/ordinal) - Cyclic dimension mapped to angular position (e.g., hours 0–23, months Jan–Dec)
- `radial` (categorical/ordinal) - Second dimension mapped to concentric rings outward from center (e.g., Mon–Sun, years)
- `value` (float) - Measured quantity encoded as cell color
- Size: 7–52 radial bins × 12–24 angular bins typical
- Example: Hourly website visits for each day of the week (7 radial × 24 angular = 168 cells)

## Notes

- Angular axis wraps continuously — 0° and 360° are adjacent, preserving cyclic continuity
- Radial axis extends outward from center; innermost ring is the first radial category
- Use a sequential colormap for single-sign data or a diverging colormap when data has a meaningful midpoint
- Label angular positions at readable intervals (e.g., 12am, 6am, 12pm, 6pm for hourly data)
- Include a colorbar legend for value interpretation
- Consider adding thin gridlines or borders between cells for readability
- Outer rings have larger area than inner rings; interpret color (not area) as the encoded channel
