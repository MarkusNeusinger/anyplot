# heatmap-adjacency: Network Adjacency Matrix Heatmap

## Description

A matrix-based representation of a network or graph where rows and columns represent nodes and cell color indicates the presence or weight of edges between them. This visualization complements node-link diagrams by excelling at revealing clusters, structural patterns, and density in large or dense networks where node-link layouts become cluttered. Reordering nodes by cluster, degree, or community membership exposes block-diagonal structure and makes group boundaries immediately visible.

## Applications

- Visualizing social network connections to detect community structure and cliques
- Displaying brain connectivity matrices in neuroscience to identify functionally linked regions
- Analyzing bilateral trade relationships between countries to reveal trading blocs
- Showing co-occurrence patterns in text analysis to find related terms or topics

## Data

- `source` (categorical) — source node identifier
- `target` (categorical) — target node identifier
- `weight` (float, optional) — edge weight or connection strength; defaults to 1 (binary presence) when absent
- Size: 20–200 nodes (adjacency matrix will be nodes × nodes)
- Example: A social network of 50 people with friendship strength scores

## Notes

- Nodes should be reorderable by cluster, degree, or community assignment to expose block-diagonal structure
- For undirected graphs the matrix is symmetric; implementations should fill both triangles
- Color intensity maps to edge weight; absent edges should use a distinct background (e.g., white or near-white)
- Optional dendrogram along axes to show hierarchical clustering of node ordering
- Include a colorbar legend showing the weight scale
- Axis tick labels should display node names; for large networks consider showing only group boundaries

## What a good version looks like

- A good version shows: a square matrix with the same nodes in the same order on rows and columns, each edge as a filled cell at its source row and target column.
- A good version shows: nodes ordered by cluster, degree or community, as the Notes ask, so that groups, where the network has them, appear as blocks along the diagonal.
- A good version shows: color intensity mapped to edge weight and explained by the color bar the Notes ask for, with absent edges in a distinct background tone that cannot be mistaken for a weak edge in either theme.
- A good version shows: both triangles filled for an undirected graph, as the Notes ask, so the matrix mirrors across its diagonal.
- A good version shows: node names as tick labels, or for a large network only labels at the group boundaries, as the Notes allow; a dendrogram along the axes, if drawn, lines up with the node order.
- Expected, not a defect: a mostly empty matrix with dense blocks, scattered cells between groups, an empty diagonal when nodes have no self-links, and an asymmetric matrix for a directed graph.
