# hive-basic: Basic Hive Plot

## Description

A hive plot arranges network nodes on radial axes based on node properties (such as degree, category, or other attributes), enabling reproducible and directly comparable network visualizations. Unlike force-directed layouts which can produce different arrangements for identical networks, hive plots always render the same network identically, solving the "hairball" problem of traditional network graphs and making structural comparisons reliable.

## Applications

- Comparing software dependency networks across versions to identify structural changes
- Analyzing social network patterns where reproducibility is required for publication or reporting
- Visualizing biological interaction networks (protein-protein, gene regulatory) for systematic analysis

## Data

- `nodes` (list of dicts) - entities with unique IDs and axis assignment attribute (e.g., role, category, or degree-based grouping)
- `edges` (list of tuples/dicts) - connections as (source_id, target_id) pairs with optional weight
- `axis_attribute` (string) - the node property used to assign nodes to axes (typically 2-3 axes)
- Size: 20-100 nodes for clear visualization; axes should have balanced node counts
- Example: A software module dependency network with nodes assigned to axes by module type (core, utility, interface)

## Notes

- Use 2-3 radial axes for clarity; more axes reduce readability
- Node position along each axis should encode a meaningful property (e.g., degree, centrality, or alphabetical order)
- Edge bundling or transparency helps with dense connections between axes

## What a good version looks like

- A good version shows: the 2-3 radial axes the Notes ask for, straight lines spreading from a common center, each labeled with the node group it carries.
- A good version shows: every node on the axis of its group, at a distance from the center set by one node property such as degree, as the Notes ask, with a caption, legend or axis note naming that property; positions follow these rules, not a layout algorithm, so the same network always draws the same way.
- A good version shows: edges as smooth curves between nodes on different axes, thinner and lighter than the nodes, and translucent or bundled where they are dense, as the Notes suggest, so bands of connections stay traceable.
- A good version shows: the basic variant's axes, nodes and curved edges, with the edge width by weight the Data allows, and no reference lines or rings, highlighted nodes or edges, callouts, duplicated axes for links within a group or second panel.
- Expected, not a defect: edges crossing and bunching near the center, nodes crowding one stretch of an axis where many share similar values, bare stretches of axis and empty canvas corners around the radial shape.
