# scatter-map-geographic: Scatter Map with Geographic Points

## Description

A geographic scatter plot that displays data points on a world or regional map, with each point positioned by its latitude and longitude coordinates. This visualization is ideal for showing spatial distributions of events, locations, or measurements across geographic areas. Points can optionally encode additional variables through size and color, enabling multi-dimensional geographic analysis at a glance.

## Applications

- Visualizing earthquake epicenters or natural disaster locations with magnitude encoded as point size
- Mapping customer or store locations with sales volume represented by point size and category by color
- Displaying sensor network readings across a geographic region with measurement values encoded in color
- Tracking wildlife sightings or species distribution with population counts as point size

## Data

- `latitude` (numeric) - Geographic latitude coordinate (-90 to 90)
- `longitude` (numeric) - Geographic longitude coordinate (-180 to 180)
- `value` (numeric, optional) - Variable for color encoding (e.g., measurement, category code)
- `size` (numeric, optional) - Variable for point size encoding (e.g., magnitude, count)
- `label` (string, optional) - Point label or identifier for tooltips
- Size: 20-500 points (works well with moderate density; too many points may require clustering)
- Example: City locations with population and region, earthquake data with magnitude and depth

## Notes

- Use an appropriate map projection (e.g., Natural Earth, Robinson for world maps; Mercator for regional/city scale)
- Include a basemap showing country boundaries, coastlines, or terrain for geographic context
- Add a color legend when color encoding is used, and a size legend when size varies
- Consider using transparency (alpha) to handle overlapping points in dense regions
- For interactive libraries, enable zoom and pan to explore point clusters
- Ensure point colors have sufficient contrast against the basemap

## What a good version looks like

- A good version shows: every point at its latitude and longitude on a basemap of country boundaries, coastlines or terrain, in a map projection suited to the mapped extent, as the Notes ask, with no point jittered or moved to separate it from its neighbors.
- A good version shows: point colors that stand out against the basemap in both themes, as the Notes ask, with the basemap kept quieter than the points.
- A good version shows: a color legend or color bar when color encodes the value and a size legend when point size varies, as the Notes ask, each naming its variable.
- A good version shows: transparency, if used as the Notes suggest, that makes dense areas read darker while stacked points remain distinguishable.
- Expected, not a defect: points piling up where events or places concentrate, large stretches of empty map, and shapes and distances distorted by the projection away from its center.
