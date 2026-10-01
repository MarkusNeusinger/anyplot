# scatter-color-mapped: Color-Mapped Scatter Plot

## Description

A scatter plot that encodes a third continuous variable using a colormap, allowing visualization of three dimensions on a 2D plane. This visualization is essential for exploring multivariate relationships where the third variable represents intensity, magnitude, or any continuous measurement. A colorbar provides a reference scale for interpreting the color values.

## Applications

- Visualizing temperature distribution across geographic coordinates
- Showing intensity or magnitude patterns in scientific measurements
- Displaying correlation strength or significance levels across data points

## Data

- `x` (numeric) - First variable plotted on the horizontal axis
- `y` (numeric) - Second variable plotted on the vertical axis
- `color` (numeric) - Third variable encoded as color intensity
- Size: 50-500 points recommended for clear visualization
- Example: Random data with a third variable representing intensity or magnitude

## Notes

- Use a perceptually uniform colormap (e.g., viridis) for accurate value interpretation
- Colorbar should have clear labels indicating the mapped variable and its units
- Points should have moderate size to ensure color visibility
- Consider transparency if points overlap significantly

## What a good version looks like

- A good version shows: one point per observation at its exact (x, y) value, its fill colored by the third variable on one continuous, perceptually uniform colormap, as the Notes ask.
- A good version shows: a color bar beside the plot labeled with the mapped variable and its units, as the Notes ask, with a range that fits the data, so the points use most of the colormap.
- A good version shows: markers large enough for their color to be read, as the Notes ask, and points at the light end of the colormap still visible against the page in both themes, for instance through a thin outline.
- A good version shows: where points overlap, transparency mild enough that the colors still match the color bar, with no point moved off its values.
- Expected, not a defect: a color pattern that is noisy rather than a smooth gradient, neighboring points of very different color, and a few extreme values at the ends of the color bar.
