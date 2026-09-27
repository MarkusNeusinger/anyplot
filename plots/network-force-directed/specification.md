# network-force-directed: Force-Directed Graph

## Description

A force-directed graph uses physics simulation to position nodes, where connected nodes attract each other and all nodes repel. This creates organic layouts that naturally reveal community structure, central nodes, and overall network topology without manual positioning. The algorithm balances attractive forces (edges pulling connected nodes together) and repulsive forces (nodes pushing apart) until reaching equilibrium.

## Applications

- Visualizing social network connections to identify communities and influential individuals
- Mapping software dependencies to understand module relationships and coupling
- Displaying knowledge graphs and ontologies showing concept relationships
- Analyzing co-occurrence networks in text analysis or biological interactions

## Data

- `nodes` (list) - Collection of entities with unique identifiers and optional labels
- `edges` (list) - Connections between nodes with source and target IDs
- `weight` (numeric, optional) - Edge weight affecting attraction strength
- Size: 20-200 nodes typical (larger networks may need filtering or aggregation)
- Example: Social network with 50 nodes representing people and edges representing friendships

## Notes

- Node size can optionally scale by degree (number of connections)
- Edge thickness can optionally represent connection strength or weight
- Use sufficient iterations to allow the layout to stabilize
- Consider node labels only for smaller networks or key nodes to avoid clutter

## What a good version looks like

- Node positions come from the force layout, not from data: there are no axes or grid, connected nodes sit close and unconnected ones apart, and a fixed seed makes the layout reproducible.
- Some edge crossings, dense hub clusters and a few peripheral nodes are expected, not defects; a perfectly planar or symmetric picture suggests fabricated data rather than a real network.
- When node size or color is used, it encodes one graph property (such as degree or community) and a legend or caption says which.
- Labels appear on hubs or key nodes, or on every node only when the network is small, and they stay readable instead of piling up inside clusters.
- Edges are thinner and lighter than the nodes, so the structure shows without an edge hairball hiding them; edge width varies only when it encodes weight.
