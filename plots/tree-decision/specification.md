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
