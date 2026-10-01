# network-transport-static: Static Transport Network Diagram

## Description

A directed network visualization for transportation systems where stations are displayed as labeled nodes and train/bus routes as directed edges. Edges display departure times, arrival times, and route identifiers. Designed for visualizing timetables, route maps, and connection patterns in rail, bus, or flight networks. This static version focuses on clear, readable presentation without interactive repositioning.

## Applications

- Visualizing regional train networks with departure and arrival times at each station
- Displaying bus route maps showing service frequency and travel times between stops
- Analyzing flight connections between airports with layover and connection information
- Planning public transit coverage by mapping routes and identifying service gaps

## Data

- `stations` (list of dicts) - nodes with `id`, `label`, `x`, `y` coordinates for positioning
- `routes` (list of dicts) - directed edges with `source_id`, `target_id`, `route_id`, `departure_time`, `arrival_time`
- Size: 8-20 stations with 15-60 routes for optimal readability
- Example: A regional rail network with 12 stations and 35 daily train services showing hourly departures

## Notes

- Station nodes should display labels clearly; size nodes to accommodate station names
- Edges must show direction with arrows indicating travel direction
- Edge labels should display route identifier and times (e.g., "RE 42 | 08:15 → 09:30")
- When multiple routes connect the same station pair, use curved or offset edges to distinguish them
- Node positioning based on provided x/y coordinates; no force-directed layout needed
- Consider color-coding routes by type (regional, express, local) or frequency
- Tooltips (where supported) should show full route details on hover

## What a good version looks like

- A good version shows: every station at its provided x and y coordinates, as the Notes ask, never rearranged by a layout algorithm or nudged to make room for labels; the coordinates may be schematic instead of geographic, so no map background is needed.
- A good version shows: every station labeled with its name on or beside a node sized to accommodate it, as the Notes ask, readable in both themes.
- A good version shows: every route as an edge with an arrowhead pointing in the travel direction, as the Notes require, the arrowhead visible at the border of the destination station.
- A good version shows: each route labeled with its route identifier and its departure and arrival times, as the Notes ask, the label placed along its own edge so that it is plain which edge it belongs to, and clear of the station nodes.
- A good version shows: routes between the same station pair as separate curved or offset edges, as the Notes ask, each with its own arrowhead and label; route colors, if used as the Notes suggest, encode route type or frequency and are named in a legend.
- Expected, not a defect: many edges and labels converging on a hub station, edge crossings, edges of very different length and a diagram dense with text, because every route carries its own label.
