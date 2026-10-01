# polar-bar: Polar Bar Chart (Wind Rose)

## Description

A bar chart arranged in a circle with bars radiating outward from the center. Each bar's angle represents a category (often direction) and length represents magnitude. Commonly used as a wind rose for meteorological data.

## Applications

- Wind direction and speed distribution
- Directional frequency analysis
- Cyclical category comparisons
- Compass-based data visualization

## Data

- `direction` (categorical) - Angular category representing compass bearing (N, NE, E, SE, S, SW, W, NW, or degrees 0-360)
- `frequency` (numeric) - Bar height or magnitude value representing counts, speed, or intensity
- Size: 8-16 categories (standard compass points) to several hundred observations
- Example: Meteorological wind direction and speed distribution dataset with directional categories and frequency counts

## Notes

- Bars extend outward from center
- Can be stacked for multiple categories (e.g., wind speed ranges)
- Often uses 8 or 16 compass directions
- Color can encode additional variables

## What a good version looks like

- A good version shows: one bar per direction or category at its own angle, extending outward from the center, as the Notes say, on a radial scale that starts at zero, so bar length stays proportional to the value.
- A good version shows: bars of one angular width, evenly spaced around the circle in compass order or the categories' cyclic order, each direction labeled at the rim.
- A good version shows: concentric gridlines with value labels, lighter than the bars and visible in both themes, so a bar's length can be read against them.
- A good version shows: stacked bars, if drawn as the Notes allow, with the segments in the same order in every bar, each segment's radial length its own value, and one color per stacked category named in a legend.
- A good version shows: color, if it encodes an additional variable as the Notes allow, explained by a legend or color bar.
- Expected, not a defect: bars of very different length, directions with a short or missing bar whose stacked segments are thin, a lopsided outline, and outer segments that cover more area than inner ones of the same value.
