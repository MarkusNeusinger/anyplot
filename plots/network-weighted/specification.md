# network-weighted: Weighted Network Graph with Edge Thickness

## Description

A weighted network graph displays relationships between entities using edge thickness to represent connection strength or weight. Unlike basic network graphs where edges are uniform, the varying line widths immediately communicate the relative importance of each relationship. This visualization makes it easy to identify strong vs weak connections, central hubs with many heavy links, and structural patterns in weighted relational data.

## Applications

- Analyzing trade flows between countries where thicker edges represent higher export/import volumes
- Visualizing communication patterns in organizations where edge weight shows message frequency between teams
- Mapping collaboration networks in research where thickness indicates number of co-authored papers
- Displaying transportation networks where edge weight represents passenger volume or freight capacity

## Data

- `nodes` (list of dicts) - entities with unique IDs and optional labels or group attributes
- `edges` (list of dicts/tuples) - connections as (source_id, target_id, weight) where weight is a positive numeric value
- `weight` (numeric) - connection strength/intensity mapped to edge thickness
- Size: 10-50 nodes for clear visualization of weighted edges without clutter
- Example: Trade network with 15 countries where edge weights represent billions of USD in annual trade volume

## Notes

- Edge thickness should scale proportionally but remain visually distinguishable (avoid too thin or too thick extremes)
- Consider a legend or annotation explaining the weight scale
- Nodes can optionally be sized by weighted degree (sum of connected edge weights)
- Use force-directed or spring layout to position nodes, allowing edge weights to influence attraction
- Avoid edge overlap where possible to keep individual weights readable

## What a good version looks like

- A good version shows: edge thickness growing with weight, as the Notes ask, so a heavier connection is always the thicker line, with the thinnest edge still visible in both themes and the thickest not burying nodes or neighboring edges.
- A good version shows: node positions from the force-directed or spring layout the Notes ask for, not from data: no axes or grid, with strongly connected nodes tending to sit closer together.
- A good version shows: a legend or annotation explaining the weight scale, if drawn as the Notes suggest, agreeing with the edges it describes; sample line widths, where it shows them, are labeled with the weights they stand for.
- A good version shows: node size, when it varies, encoding weighted degree as the Notes allow, and node color, when it varies, encoding a group attribute, each named in a legend or caption.
- A good version shows: edges kept apart where possible, as the Notes ask, so each one's thickness can be read along its length, with nodes and their labels drawn on top of the edges.
- Expected, not a defect: some edge crossings, thick edges converging on hubs, a few heavy edges dominating many thin ones and peripheral nodes held by a single light link.
