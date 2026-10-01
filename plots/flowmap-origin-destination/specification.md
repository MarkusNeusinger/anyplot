# flowmap-origin-destination: Origin-Destination Flow Map

## Description

An origin-destination flow map visualizes movement or transfer between geographic locations using curved arcs overlaid on a map. Each arc connects an origin point to a destination point, with line thickness proportional to the flow magnitude. This visualization excels at revealing spatial patterns in migration, trade, or travel data, making it easy to identify major corridors, hub locations, and directional imbalances in movement between places.

## Applications

- Visualizing international migration flows showing population movement between countries or regions
- Analyzing trade routes displaying import/export volumes between ports or economic centers
- Mapping commuter patterns showing daily travel flows between residential areas and employment centers
- Displaying supply chain logistics illustrating shipment volumes between distribution centers and retail locations

## Data

- `origin_lat` (numeric) - Latitude coordinate of flow origin (-90 to 90)
- `origin_lon` (numeric) - Longitude coordinate of flow origin (-180 to 180)
- `dest_lat` (numeric) - Latitude coordinate of flow destination (-90 to 90)
- `dest_lon` (numeric) - Longitude coordinate of flow destination (-180 to 180)
- `flow` (numeric) - Flow magnitude or volume (determines arc thickness)
- `origin_name` (string, optional) - Label for origin location
- `dest_name` (string, optional) - Label for destination location
- Size: 20-200 flows (fewer flows for clarity; too many obscure patterns)
- Example: Migration flows between world capitals, trade volumes between major ports

## Notes

- Use curved arcs (Bezier curves or great circle paths) to connect origin and destination points
- Line width should be proportional to flow magnitude for visual comparison
- Apply transparency (alpha 0.4-0.7) to handle overlapping arcs in dense flow networks
- Consider using a color gradient to encode flow direction or magnitude
- Include a basemap with country boundaries or coastlines for geographic context
- For interactive libraries, add hover tooltips showing exact flow values and location names
- Optionally animate arcs to show flow direction using moving particles or progressive drawing

## What a good version looks like

- A good version shows: one curved arc per flow, as the Notes ask, a Bezier curve or a great-circle path, whose two ends sit exactly on the origin and destination coordinates.
- A good version shows: arc width proportional to the flow magnitude, as the Notes ask, so the major corridors stand out from the minor ones; a width legend or key, if drawn, ties widths to flow values.
- A good version shows: translucent arcs, as the Notes ask, so thin flows remain visible where they pass under or beside thick ones.
- A good version shows: a color gradient, if used as the Notes suggest, that encodes flow direction or magnitude and is explained by a legend or caption saying which.
- A good version shows: a basemap with country boundaries or coastlines beneath the arcs, as the Notes ask, quieter than the arcs so the flow pattern leads.
- Expected, not a defect: arcs crossing and overlapping where many flows converge on a hub, a few dominant corridors beside many thin arcs, and arcs sweeping over land or sea that lies off the real route of the movement.
