# network-basic: Basic Network Graph

## Description

A network graph (node-link diagram) visualizes relationships between entities as nodes connected by edges. It reveals the structure of connections, clusters, and central nodes in relational data. Network graphs are essential for understanding complex systems where relationships matter as much as the entities themselves, making hidden patterns of connectivity visible at a glance.

## Applications

- Analyzing social networks to identify influential individuals, communities, and information flow patterns
- Mapping citation networks in academic research to discover influential papers and emerging research clusters
- Visualizing software architecture dependencies to understand module coupling and identify potential refactoring targets

## Data

- `nodes` (list of dicts) - entities with unique IDs and optional attributes like label or group
- `edges` (list of tuples/dicts) - connections as (source_id, target_id) pairs with optional weight
- Size: 10-50 nodes for clear static visualization (larger networks require interactive exploration)
- Example: A small social network with 20 people and their friendship connections

## Notes

- Use force-directed or spring layout for automatic node positioning
- Node size can optionally encode degree (number of connections)
- Keep the network sparse enough that individual connections remain visible
- Labels should be legible without overlapping other elements

## What a good version looks like

- A good version shows: node positions from the force-directed or spring layout the Notes ask for, not from data: no axes or grid, connected nodes close together and unconnected ones apart.
- Expected, not a defect: some edge crossings, a dense cluster around a hub, peripheral nodes with a single connection and uneven gaps between groups.
- A good version shows: edges thinner and lighter than the nodes and sparse enough that each connection can be followed from one node to the other, as the Notes ask, instead of merging into a hairball.
- A good version shows: node labels, where drawn, readable and clear of other labels, nodes and edges, as the Notes ask.
- A good version shows: the basic variant's nodes and links only, with the node size by degree, the node color by group and the edge width by weight that the Notes and Data allow, each named in a legend or caption if used, and no reference lines, highlighted nodes or edges, community hulls, callouts or second panel.
