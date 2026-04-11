# scatter-embedding: t-SNE and UMAP Embedding Visualization

## Description

A scatter plot displaying high-dimensional data projected into 2D space using non-linear dimensionality reduction techniques such as t-SNE or UMAP. Points are colored by cluster or class label, revealing groupings and latent structure in the data. This is a standard visualization in machine learning for exploring embeddings, single-cell RNA-seq data, and NLP document clustering, helping practitioners verify that learned representations capture meaningful distinctions.

## Applications

- Visualizing cell-type clusters in single-cell RNA-seq data after dimensionality reduction in bioinformatics workflows
- Exploring word or document embeddings from NLP models to verify semantic groupings and detect outliers
- Inspecting latent space structure of autoencoders or variational autoencoders (VAEs) to assess representation quality
- Quality-checking clustering results from K-means or DBSCAN by overlaying cluster assignments on the 2D projection

## Data

- `x` (float) — First embedding dimension (e.g., t-SNE 1 or UMAP 1)
- `y` (float) — Second embedding dimension (e.g., t-SNE 2 or UMAP 2)
- `label` (categorical) — Cluster or class assignment for coloring points
- Size: 500–5000 points typical
- Example: Synthetic clustered data with 5–10 groups projected via t-SNE or UMAP

## Notes

- Color each cluster/class with a distinct, colorblind-accessible color and include a legend mapping colors to labels
- Optionally annotate cluster centroids with the cluster label text
- Use moderate point size with slight transparency (alpha) to handle overlapping points in dense regions
- Include a subtitle noting the algorithm and key parameter (e.g., "t-SNE (perplexity=30)" or "UMAP (n_neighbors=15)")
- Axes represent embedding dimensions and typically should not have tick labels, as the coordinates are not directly interpretable
