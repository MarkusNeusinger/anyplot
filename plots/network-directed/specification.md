# network-directed: Directed Network Graph

## Description

A directed network graph visualizes relationships between entities using nodes connected by edges with arrows, indicating the direction of relationships or flow. Unlike undirected graphs, directed graphs reveal asymmetric relationships such as dependencies, hierarchies, or information flow. The arrows clearly communicate which entity points to which, making cause-and-effect relationships and directional dependencies immediately visible.

## Applications

- Mapping software module dependencies to understand build order and identify circular dependencies
- Visualizing citation networks where arrows show which papers cite which others
- Displaying organizational reporting structures or workflow approval chains
- Analyzing web page link structures to understand navigation patterns and page authority

## Data

- `nodes` (list of dicts) - entities with unique IDs and optional attributes like label or group
- `edges` (list of tuples/dicts) - directed connections as (source_id, target_id) pairs where arrows point from source to target
- `weight` (numeric, optional) - edge weight that can affect edge and arrow thickness
- Size: 10-50 nodes for clear static visualization (larger networks require interactive exploration)
- Example: Software package dependencies where arrows show import direction

## Notes

- Arrows should be clearly visible and appropriately sized relative to node size
- Consider curved edges when nodes have bidirectional connections to avoid arrow overlap
- Node position can use force-directed layout, hierarchical layout, or circular layout depending on data structure
- Arrow style (filled, open, curved) should be consistent throughout the graph

## What a good version looks like

- A good version shows: every edge ending in an arrowhead that points from source to target, visible at the border of the target node instead of hidden beneath it and sized in proportion to the nodes, as the Notes ask.
- A good version shows: a consistent arrow style throughout the graph, as the Notes ask; where edges differ in thickness, the difference encodes the optional weight by one rule, as the Data allows.
- A good version shows: two nodes linked in both directions, if the data has such a pair, drawn so that both arrowheads can be told apart, for example as two curved edges, as the Notes suggest.
- A good version shows: node positions from a force-directed, hierarchical or circular layout, as the Notes allow, not from data: no axes or grid, and edges thinner and lighter than the nodes they join.
- A good version shows: node labels, where drawn, readable and attached to their nodes, with edges and arrowheads kept out of the text.
- Expected, not a defect: edge crossings, edges that run against the main direction where the data has cycles, arrowheads gathering around a node with many incoming edges, and nodes with only incoming or only outgoing edges.
