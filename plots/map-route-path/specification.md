# map-route-path: Route Path Map

## Description

A geographic map visualization showing a connected path or route between sequential waypoints. Unlike scatter maps that display discrete points, this plot connects coordinates in order to reveal journeys, tracks, and navigation paths. Ideal for GPS data, delivery routes, and travel visualization where the sequence and continuity of movement matters.

## Applications

- Visualizing GPS tracks from fitness activities like running, hiking, or cycling routes
- Mapping delivery or logistics routes to analyze coverage and efficiency
- Displaying historical journeys or expedition paths for storytelling and education
- Reconstructing vehicle trajectories from telematics or tracking data

## Data

- `lat` (numeric) - Latitude coordinate for each waypoint (-90 to 90)
- `lon` (numeric) - Longitude coordinate for each waypoint (-180 to 180)
- `sequence` (integer) - Point order defining the path direction
- `timestamp` (datetime, optional) - Time at each waypoint for color encoding or animation
- Size: 50-1000 waypoints for smooth path visualization
- Example: A hiking trail GPS track with coordinates recorded every few seconds

## Notes

- Connect waypoints in sequence order with continuous lines
- Use distinct markers for start and end points (e.g., green circle for start, red square for end)
- Consider color gradients along the path to show time progression, speed, or elevation
- Optional direction arrows along the path indicate travel direction
- Apply line smoothing or simplification for noisy GPS data
- Include a geographic basemap (streets, terrain, or satellite) for spatial context
- For interactive libraries, enable zoom and pan to explore route details

## What a good version looks like

- A good version shows: one continuous line through the waypoints in sequence order, as the Notes ask, each vertex at its latitude and longitude and no segment joining points that are not consecutive.
- A good version shows: distinct markers for the start and the end of the route, as the Notes ask, told apart by shape or color so that a reader can tell at which end the journey began.
- A good version shows: a color gradient along the path, if used as the Notes suggest, following time progression, speed or elevation and explained by a color bar or legend that names the variable.
- A good version shows: direction arrows, if drawn as the Notes allow, pointing along the direction of travel and sparse enough to leave the line visible.
- A good version shows: a geographic basemap of streets, terrain or satellite imagery, as the Notes ask, quieter than the route, with the view fitted to the route's extent.
- Expected, not a defect: a path that crosses or retraces itself on loops and out-and-back legs, unevenly spaced waypoints, small wiggles left after the smoothing or simplification the Notes ask for, and a route filling only an irregular part of the frame.
