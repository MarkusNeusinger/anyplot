# sankey-basic: Basic Sankey Diagram

## Description

A Sankey diagram visualizes flow or transfer between nodes using links with widths proportional to flow values. It excels at showing how quantities distribute from sources to destinations, revealing patterns in resource allocation, process flows, and system transitions. The diagram makes it easy to identify major pathways and compare relative magnitudes of different flows.

## Applications

- Visualizing energy flows from sources (coal, gas, nuclear) through transformation to end uses (heating, transport, industry)
- Tracking budget allocations from revenue sources through departments to specific expense categories
- Analyzing website traffic paths from entry pages through navigation to conversion or exit points

## Data

- `source` (categorical) - the origin node of each flow
- `target` (categorical) - the destination node of each flow
- `value` (numeric) - the magnitude of flow between source and target
- Size: 5-50 flows (too many flows reduce readability)
- Example: Energy flow data with sources like "Coal", "Gas", "Nuclear" flowing to sectors like "Residential", "Commercial", "Industrial"

## Notes

- Ensure no circular flows (source cannot equal target in the same link)
- Node labels should be clearly visible and not overlap with links
- Use distinct colors for different source categories or flow types
- Link opacity can help when flows cross over each other

## What a good version looks like

- A good version shows: every flow as a link from its source node to its target node, its width proportional to its value along its whole length, and each node as a bar as tall as the links attached to it, with no link from a node back to itself.
- A good version shows: node and link order set by the layout, not by data: nodes grouped in stages along the flow direction, in any vertical order; only the link widths and bar heights carry values.
- A good version shows: every node named by a label beside or on its bar, with or without the node's total, and clear of the links, as the Notes ask.
- A good version shows: distinct colors for the source categories or flow types, as the Notes ask, carried by the links so each can be followed from end to end; the link translucency the Notes allow, if used, keeps crossing links distinguishable in both themes.
- A good version shows: the basic variant's single flow diagram: besides the node bars, their labels and the links, no highlighted links or nodes, reference lines, callouts or annotations of a dominant pathway, link colors from a second variable, or second diagram or panel.
- Expected, not a defect: links that cross, blended color where translucent links overlap, hair-thin links for small flows, and node bars of very different height, including nodes that only send or only receive.
