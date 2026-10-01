# bubble-map-geographic: Bubble Map with Sized Geographic Markers

## Description

A geographic bubble map where markers are sized proportionally to quantitative data values at each location. Unlike scatter maps where size is optional, bubble maps use marker size as the primary visual encoding to show data magnitude across geographic regions. This visualization makes it immediately apparent where high and low values occur spatially, enabling intuitive comparison of quantities across locations.

## Applications

- Displaying city populations on a map with bubble size representing population magnitude
- Showing sales volume by store location with proportionally sized markers
- Visualizing earthquake magnitudes across a region with size indicating severity
- Mapping disease case counts by city or region with bubble size showing outbreak intensity

## Data

- `latitude` (numeric) - Geographic latitude coordinate (-90 to 90)
- `longitude` (numeric) - Geographic longitude coordinate (-180 to 180)
- `value` (numeric) - Quantitative variable for size encoding (e.g., population, sales, count)
- `label` (string, optional) - Location name or identifier for tooltips
- `category` (string, optional) - Categorical variable for color grouping
- Size: 15-150 points (fewer points than scatter maps to avoid excessive overlap)
- Example: World cities with population, regional sales data by location

## Notes

- Scale bubble area (not radius) proportionally to data values for accurate perception
- Use a size legend showing the relationship between bubble size and data values
- Apply transparency (alpha ~0.5-0.7) to handle overlapping bubbles in dense regions
- Include geographic context with country boundaries or coastlines as basemap
- Consider using a minimum bubble size to ensure small values remain visible
- For interactive libraries, enable hover tooltips showing exact values and location names

## What a good version looks like

- A good version shows: every bubble centered on its latitude and longitude over a basemap of country boundaries or coastlines, as the Notes ask, with the basemap quieter than the bubbles and no bubble moved off its location to reduce overlap.
- A good version shows: bubble area, not radius, proportional to the value, as the Notes ask, so a value twice as large has twice the area; a minimum bubble size, if used as the Notes suggest, keeps the smallest values visible.
- A good version shows: a size legend, as the Notes ask, with a few reference bubbles drawn like the data marks and labeled in the value's units.
- A good version shows: translucent fills where bubbles overlap, as the Notes ask, so that a small bubble is never hidden inside a large one; drawing smaller bubbles above larger ones or adding a thin outline helps where the overlap is dense.
- A good version shows: bubble color, if the optional category is used, as one distinct color per category named in a legend separate from the size legend.
- Expected, not a defect: bubbles overlapping where locations lie close together, such as neighboring cities, large bubbles covering part of the coastline or borders beneath them, and wide stretches of empty map.
