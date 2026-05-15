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
