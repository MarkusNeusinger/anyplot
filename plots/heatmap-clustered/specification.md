# heatmap-clustered: Clustered Heatmap

## Description

A heatmap with hierarchical clustering dendrograms on both rows and columns, showing both data values and their hierarchical relationships. Rows and columns are automatically reordered based on clustering results to reveal natural groupings in the data. Essential for discovering patterns in high-dimensional data where similar observations or variables should be visually grouped together.

## Applications

- Gene expression analysis identifying co-expressed genes and sample clusters
- Customer segmentation revealing behavioral patterns and market segments
- Feature correlation analysis with automatic grouping of related variables
- Biological pathway analysis clustering related proteins or metabolites

## Data

- `matrix` (numeric) - 2D matrix of values for heatmap cells
- `row_labels` (string) - labels for matrix rows
- `column_labels` (string) - labels for matrix columns
- Size: 10-100 rows, 10-50 columns (larger matrices may have readability issues)

## Notes

- Display dendrograms on both rows and columns (clustermap style)
- Reorder rows and columns according to hierarchical clustering results
- Use a diverging colormap for data centered around zero
- Include a colorbar legend showing the value scale
- Consider adding row/column color bars for group annotations
- Ward's method with Euclidean distance is a common default for clustering

## What a good version looks like

- A good version shows: a dendrogram along the rows and another along the columns, as the Notes ask, each leaf lined up with its row or column of cells.
- A good version shows: rows and columns reordered by the clustering, as the Notes ask, so similar rows and columns sit next to each other and blocks of like values emerge, with every label still at its own row or column.
- A good version shows: a diverging colormap centered on zero when the data is centered around zero, as the Notes ask, and a color bar showing the value scale.
- A good version shows: dendrogram branches whose merge heights can be told apart, drawn in lines visible in both themes and taking a smaller share of the figure than the matrix.
- A good version shows: row or column color strips for group annotations, if drawn, aligned cell by cell with the rows or columns they annotate and explained by a legend.
- Expected, not a defect: a row and column order that looks arbitrary by label, blocks of unequal size, rows that fit no cluster, and no in-cell numbers on a large matrix.
