# hexbin-map-geographic: Hexagonal Binning Map

## Description

A geographic map visualization that aggregates point data into hexagonal cells, displaying density or aggregated values per cell using color intensity. Unlike continuous heatmaps that use kernel density estimation, hexbin maps provide discrete binning that clearly shows data aggregation boundaries. The hexagonal grid is superior to square grids due to isotropy (equal distance to neighboring cells) and better visual continuity, making it ideal for spatial statistics and urban data analysis.

## Applications

- Aggregating taxi pickup/dropoff locations to identify transportation demand zones in urban mobility analysis
- Visualizing species observation density across geographic regions for ecological monitoring
- Displaying crime incident patterns with hexagonal aggregation for law enforcement resource allocation
- Mapping sensor readings or IoT device measurements aggregated into geographic zones

## Data

- `lat` (numeric) - Latitude coordinate (-90 to 90)
- `lon` (numeric) - Longitude coordinate (-180 to 180)
- `value` (numeric, optional) - Value to aggregate per cell (defaults to count when not provided)
- Size: 1,000-100,000+ points (designed for large datasets where individual points would overlap)
- Example: GPS coordinates of events with optional measurement values, taxi trip endpoints, species sightings

## Notes

- Hexagon size should be configurable to balance detail vs. aggregation (larger hexagons for overview, smaller for detailed patterns)
- Support aggregation methods: count (default), sum, and mean of values
- Use a sequential colormap (e.g., viridis, plasma, YlOrRd) with a color legend showing the scale
- Overlay hexagons on a base map showing geographic context (coastlines, country boundaries, or street map)
- Apply transparency to hexagons to allow base map features to show through
- For interactive libraries, enable hover tooltips showing cell statistics (count, sum, mean, coordinates)

## What a good version looks like

- A good version shows: the points aggregated into a regular grid of equal hexagons with shared edges, each cell lying over the locations of the points it aggregates and colored by its count or aggregated value.
- A good version shows: a hexagon size that balances detail against aggregation, as the Notes ask: the spatial pattern is visible, with neither a handful of giant cells nor a scatter of tiny ones that mostly hold a single point.
- A good version shows: a sequential colormap with a color legend showing the scale, as the Notes ask, that names the statistic drawn (count, sum or mean).
- A good version shows: the hexagons overlaid on a base map of coastlines, country boundaries or streets and translucent enough for its features to show through, as the Notes ask.
- Expected, not a defect: gaps in the grid where no points fall, cell edges that cut across coastlines and borders, a few very dark cells among many pale ones, and hexagons that look stretched or unequal under the map projection.
