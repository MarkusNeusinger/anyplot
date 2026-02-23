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
- `weights` (numeric, optional) - Edge weights affecting arc thickness or height
- Size: 10-50 nodes typical for readability
- Example: Character interactions in a novel — nodes as characters, edges as dialogue exchanges

## Notes

- Arcs should curve above the horizontal axis with height proportional to the distance between connected nodes
- Use semi-transparent arcs when many connections overlap
- Node labels should be readable along the axis
- Consider color coding edges by type or weight when applicable
