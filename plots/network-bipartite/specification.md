# network-bipartite: Bipartite Network Graph

## Description

A bipartite network graph visualizes relationships between two distinct sets of entities, where edges only connect nodes from different sets — never within the same set. The two node groups are arranged in separate columns or rows, making the two-mode structure immediately apparent. This layout is fundamental for understanding cross-category relationships, revealing which entities from one set are linked to which entities in the other, and exposing patterns like hubs, clusters, and isolated nodes.

## Applications

- Author-paper affiliation networks in bibliometrics showing which researchers contributed to which publications
- User-product purchase or recommendation networks revealing consumption patterns and shared preferences
- Gene-disease association networks in bioinformatics mapping known links between genetic markers and conditions
- Student-course enrollment visualization displaying registration patterns across academic programs

## Data

- `source` (str) — node identifier from set A (e.g., authors, users, genes)
- `target` (str) — node identifier from set B (e.g., papers, products, diseases)
- `weight` (float, optional) — edge weight representing connection strength or frequency
- Size: 10–50 nodes per set, 20–200 edges
- Example: A network of 15 researchers and 20 papers, with edges connecting each author to their publications

## Notes

- Arrange the two node sets in clearly separated columns (left/right) or rows (top/bottom)
- Color nodes by set membership to reinforce the bipartite structure
- Node size should encode degree (number of connections) to highlight hubs
- Edge width or opacity can encode weight when weight data is provided
- Labels should be legible and positioned to avoid overlap with edges
- Keep the layout clean — use straight or slightly curved edges to reduce visual clutter

## What a good version looks like

- A good version shows: the two node sets in two clearly separated parallel columns or rows, as the Notes ask, with every edge running from one set to the other and none within a set; the order of nodes inside a set comes from the layout, not from data, so there are no axes or grid.
- A good version shows: nodes colored by set membership, as the Notes ask, with a legend or a heading on each column or row naming the set.
- A good version shows: node size growing with degree, as the Notes ask, so hubs stand out and the least connected nodes stay visible in both themes.
- A good version shows: straight or slightly curved edges, as the Notes ask, thinner and lighter than the nodes; edge width or opacity varies only when it encodes weight, and the faintest edge stays visible in both themes.
- A good version shows: node labels next to their nodes and clear of the edges, as the Notes ask, for instance on the outer side of each column or row.
- Expected, not a defect: edge crossings between the two sets, a dense band in the middle where many edges meet, nodes of very different size and nodes with a single connection.
