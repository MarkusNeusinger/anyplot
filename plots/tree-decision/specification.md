# tree-decision: Decision Tree Visualization with Probabilities

## Description

A tree-structured diagram for sequential decision analysis, displaying decision nodes (squares), chance nodes (circles), and terminal outcome nodes (triangles) connected by branching paths. Each chance branch is labeled with probabilities, terminal nodes show payoff values, and Expected Monetary Values (EMV) are calculated via rollback at each node. Rejected (pruned) branches are visually marked, making it easy to trace the optimal decision path through a multi-stage problem.

## Applications

- Business strategy: evaluating whether to launch a new product line by comparing investment options under uncertain market conditions
- Medical decision-making: choosing between treatment pathways based on probability of outcomes and quality-adjusted life years
- Project management: analyzing go/no-go decisions for R&D projects with uncertain technical success and market demand
- Operations research: optimizing sequential decisions such as equipment replacement or capacity expansion under uncertainty

## Data

- `node_id` (string) - unique identifier for each node in the tree
- `node_type` (categorical: decision/chance/terminal) - the type of node determining its shape
- `parent_id` (string) - identifier of the parent node (null for root)
- `branch_label` (string) - label for the branch connecting to this node (option name or probability)
- `probability` (float, 0-1) - probability assigned to chance branches (null for decision branches)
- `payoff` (float) - monetary or utility value at terminal nodes
- `emv` (float) - expected monetary value calculated via rollback at decision and chance nodes
- `pruned` (boolean) - whether this branch is rejected in the optimal solution
- Size: 10-30 nodes typical for a readable decision tree
- Example: a two-stage investment decision — first choose to invest or not, then face uncertain outcomes (high/low demand) with associated probabilities and payoffs

## Notes

- Decision nodes should be rendered as squares, chance nodes as circles, and terminal nodes as right-pointing triangles
- Left-to-right layout is preferred for readability
- Pruned branches should be marked with a double-strike or cross mark and rendered with reduced opacity or a dashed line
- EMV values should be displayed inside or adjacent to each non-terminal node
- Probabilities on chance branches should sum to 1.0 for each chance node
- Use distinct colors for decision vs. chance nodes for quick visual identification
- Branch labels for decision nodes should show option names; branch labels for chance nodes should show probability values

## What a good version looks like

- A good version shows: decision nodes as squares, chance nodes as circles and terminal nodes as right-pointing triangles, as the Notes ask, with decision and chance nodes in distinct colors.
- A good version shows: the tree typically growing from the root at the left to the terminal nodes at the right, the layout the Notes prefer, with node positions from the tree layout, not from data: no axes or grid.
- A good version shows: every branch labeled, with the option name on a decision node's branches and the probability on a chance node's branches, as the Notes ask, each label beside its branch and not struck through by it.
- A good version shows: the EMV inside or next to every decision and chance node and the payoff at every terminal node, as the Notes and Description ask, with the probabilities at each chance node summing to 1.0.
- A good version shows: every pruned branch marked with a double-strike or cross mark and drawn fainter or dashed, as the Notes ask, so the optimal path stands out as the unmarked, solid route.
- Expected, not a defect: branches of unequal depth, terminal nodes at different distances from the root, a text-heavy diagram, empty canvas corners beside the tree, and pruned subtrees that are harder to read than the optimal path.
