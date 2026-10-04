# arc-basic: Basic Arc Diagram

## Description

An arc diagram arranges nodes along a single horizontal line and draws connections between them as curved arcs above the line. This layout excels at revealing patterns in sequential or ordered data while minimizing visual clutter compared to force-directed layouts. Arc height typically indicates the distance between connected nodes, making it easy to spot long-range versus short-range connections.

## Applications

- Visualizing narrative flow and character interactions in stories or scripts
- Showing gene interactions along a chromosome in genomic analysis
- Displaying word co-occurrences or dependencies in text analysis
- Mapping sequential process dependencies in workflows

## Data

- `nodes` (list) - Ordered sequence of entity names or identifiers
- `edges` (list of tuples) - Pairs of node indices or names indicating connections
- `weights` (numeric, optional) - Edge weights affecting arc thickness
- Size: 10-50 nodes typical for readability
- Example: Character interactions in a novel — nodes as characters, edges as dialogue exchanges

## Notes

- Arcs should curve above the horizontal axis with height proportional to the distance between connected nodes
- Use semi-transparent arcs when many connections overlap
- Node labels should be readable along the axis
- Consider color coding edges by type or weight when applicable

## What a good version looks like

- A good version shows: all nodes on one horizontal line in the order the data gives, a position that comes from the sequence and not from data values, so there are no value axes or grid.
- A good version shows: every connection as a smooth arc above the line joining its two nodes, its height growing with the distance between them, as the Notes ask, so long-range links rise above short-range ones.
- A good version shows: semi-transparent arcs where many connections overlap, as the Notes ask, so that single arcs can still be followed to both end nodes in both themes.
- A good version shows: each node's label at its node along the line, readable, as the Notes ask, and not running into its neighbors.
- A good version shows: the basic variant's single row of nodes and its arcs above it, with the arc thickness by weight and the arc color by type or weight that the Data and Notes allow, and no reference lines, highlighted nodes or arcs, callouts, node sizing by a metric, arcs below the line or a second row.
- Expected, not a defect: arcs that cross and nest, one or two tall arcs spanning most of the line above many low ones, arcs piling up at a well-connected node and empty space beside the tallest arcs.
