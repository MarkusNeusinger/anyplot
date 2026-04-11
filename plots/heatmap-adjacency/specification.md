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
