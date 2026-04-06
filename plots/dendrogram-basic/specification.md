# dendrogram-basic: Basic Dendrogram

## Description

A dendrogram visualizes hierarchical clustering by showing how data points or clusters merge at different distance levels. The tree-like structure reveals relationships and similarity between items, with branch heights indicating the distance at which clusters merge. This visualization is essential for understanding the hierarchical structure in data and identifying natural groupings.

## Applications

- Visualizing results from hierarchical clustering algorithms (e.g., agglomerative clustering)
- Gene expression analysis showing relationships between samples or genes
- Document clustering to reveal topic hierarchies and content similarity
- Customer segmentation analysis showing how customer groups relate to each other

## Data

- `features` (numeric matrix) - measurement values for each item (e.g., petal length, sepal width), used to compute distances
- `labels` (string) - names or identifiers for each item being clustered
- `linkage_matrix` (numeric) - output from scipy's linkage function containing merge distances, computed from features
- Size: 10-50 items recommended for readable dendrograms
- Example: hierarchical clustering of iris flower species by measurements

## Notes

- Use scipy.cluster.hierarchy for computing linkage and plotting dendrograms
- Vertical orientation is most common, but horizontal works well for long labels
- Branch heights should be proportional to merge distances for accurate interpretation
- Consider using truncation for very large datasets to improve readability
