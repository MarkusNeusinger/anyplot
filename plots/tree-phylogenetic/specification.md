# tree-phylogenetic: Phylogenetic Tree Diagram

## Description

A phylogenetic tree (evolutionary tree) visualization showing hierarchical relationships between species or sequences, with branch lengths proportional to evolutionary distance. This diagram reveals how organisms or genes evolved from common ancestors, with longer branches indicating greater divergence. Phylogenetic trees are essential for understanding evolutionary history, taxonomy, and molecular biology relationships.

## Applications

- Visualizing evolutionary relationships between species based on genetic sequence analysis
- Displaying taxonomic classification hierarchies in biology and ecology studies
- Showing protein or gene family evolution and divergence patterns
- Comparing pathogen strains to understand disease transmission and mutation patterns

## Data

- `newick_string` (string) - tree structure in Newick format with branch lengths
- `species_names` (string) - labels for leaf nodes representing species or sequences
- `branch_lengths` (numeric) - evolutionary distances between nodes
- Size: 5-50 leaf nodes recommended for readable trees
- Example: phylogenetic tree of primate species based on mitochondrial DNA

## Notes

- Branch lengths should be drawn proportionally to show evolutionary distance accurately
- Consider both rectangular and circular (radial) tree layouts
- Add a scale bar or a labeled branch-length axis to indicate branch length units (e.g., substitutions per site)
- Color-code clades or highlight specific lineages for emphasis

## What a good version looks like

- A good version shows: each branch drawn with a length proportional to its branch length, as the Notes ask, along the horizontal direction in a rectangular layout or the radial direction in a circular one; branch lengths are the data and are never equalized to line the tips up.
- A good version shows: a rectangular layout with right-angled branches or a circular one, as the Notes allow; the order and spacing of the tips come from the layout, so only a branch's own length, never the gap between tips, stands for evolutionary distance.
- A good version shows: every tip labeled with its species or sequence name at the end of its branch, readable in both themes.
- A good version shows: a scale bar or a labeled branch-length axis, as the Notes ask, labeled with the branch length unit and drawn to the same scale as the branches.
- A good version shows: clades color-coded or a specific lineage highlighted, as the Notes ask, the color covering all branches of the clade and explained by a legend or clade labels.
- Expected, not a defect: tips that end at different distances from the root, very short internal branches that nearly merge neighboring splits, one long branch that stretches the scale, a lopsided, ladder-like tree and empty space beside short clades.
