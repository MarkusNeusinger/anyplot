# silhouette-basic: Silhouette Plot

## Description

A silhouette plot visualizes the quality of clustering results by showing the silhouette coefficient for each sample, grouped by cluster assignment. Each horizontal bar represents a sample's silhouette score (-1 to 1), where positive values indicate good cluster membership and negative values suggest potential misclassification. This visualization helps evaluate cluster cohesion (how similar samples are to their own cluster) and separation (how distinct they are from neighboring clusters).

## Applications

- Evaluating K-means, hierarchical, or other clustering algorithm results
- Comparing different numbers of clusters to find optimal k value
- Identifying poorly clustered or potentially misclassified samples
- Validating cluster assignments before downstream analysis

## Data

- `samples` (numeric) - feature vectors for each data point to be clustered
- `cluster_labels` (integer) - cluster assignment for each sample (0 to k-1)
- `silhouette_values` (numeric) - silhouette coefficient per sample (-1 to 1)
- Size: 50-500 samples with 2-10 clusters for readable visualization
- Example: clustering iris dataset into 3 species groups

## Notes

- Display horizontal bars for each sample's silhouette score, sorted within each cluster
- Group samples by cluster with distinct colors per cluster
- Include vertical line at average silhouette score for reference
- Annotate each cluster section with its average silhouette score
- Use sklearn.metrics.silhouette_samples for computing individual scores
- Clusters with consistently high scores (close to 1) indicate well-separated groups

## What a good version looks like

- A good version shows: one horizontal bar per sample from zero to its silhouette score, a negative score extending to the other side of zero, sorted within each cluster, as the Notes ask; the order along the bar axis is that sort, not a data value.
- A good version shows: the samples grouped by cluster, each cluster in its own color, as the Notes ask, the blocks told apart from their neighbors by color or a gap so the thickness of a block reads as the size of its cluster.
- A good version shows: a vertical line at the average silhouette score, as the Notes ask, running across all clusters, told apart from the bars and visible in both themes.
- A good version shows: each cluster section annotated with its average silhouette score, as the Notes ask, the text beside its own block and clear of the bars.
- A good version shows: the basic variant's single clustering: the sample bars, the average line and the cluster annotations the Notes ask for, and no other reference lines, highlighted samples or bands, further callouts, companion scatter panel or comparison across cluster counts.
- Expected, not a defect: negative scores, clusters of unequal thickness, blocks that taper to a thin tip, a cluster that lies entirely short of the average line, and bars so thin in a large sample that a block reads as one filled shape.
