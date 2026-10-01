# ma-differential-expression: MA Plot for Differential Expression

## Description

An MA plot (M-versus-A plot) visualizes the relationship between log fold change (M) and mean average expression (A) when comparing two experimental conditions. Each point represents a gene or feature, with significantly differentially expressed genes highlighted. This plot is a standard diagnostic tool in RNA-seq and microarray analysis for assessing differential expression results and detecting systematic expression-dependent bias.

## Applications

- Identifying differentially expressed genes between treatment and control conditions in RNA-seq experiments
- Assessing normalization quality and detecting expression-dependent bias in microarray data
- Comparing treatment versus control conditions in transcriptomics studies
- Quality control in high-throughput genomics pipelines to verify fold-change distributions

## Data

- `mean_expression` (numeric) - A value: average log expression level across both conditions (x-axis)
- `log_fold_change` (numeric) - M value: log2 fold change between conditions (y-axis)
- `significant` (boolean) - Whether the gene passes the significance threshold (e.g., adjusted p < 0.05)
- `gene_name` (string, optional) - Gene identifier for labeling notable points
- Size: 10,000-20,000 genes typical for whole-transcriptome experiments
- Example: DESeq2 or edgeR differential expression results with baseMean, log2FoldChange, and padj columns

## Notes

- Highlight significant genes (adjusted p < 0.05) in a distinct color (e.g., red) against non-significant genes in gray
- Draw a horizontal reference line at M = 0 (no change) and dashed lines at M = +1 and M = -1 (2-fold change thresholds)
- Include a LOESS smoothing curve to reveal any systematic expression-dependent bias
- Use transparency (alpha ~0.3) to handle overplotting in dense regions
- Optionally label a small number of top differentially expressed genes by name

## What a good version looks like

- A good version shows: one point per gene at its mean expression on the x axis and its log fold change on the y axis, every point at its values and never jittered or displaced to thin the cloud.
- A good version shows: significant genes in a distinct color against the non-significant genes in gray, as the Notes ask, drawn so they are not buried under the gray mass.
- A good version shows: a horizontal reference line at no change and dashed lines at the two fold-change thresholds above and below it, as the Notes ask, running across the whole expression range and visible through the points in both themes.
- A good version shows: a LOESS curve through the cloud, as the Notes ask, following the local average of the fold changes and distinguishable from the reference line and from the points.
- A good version shows: transparency on the points, as the Notes ask, so the dense band reads as density, and gene names, if drawn, on only a small number of top genes, as the Notes allow.
- Expected, not a defect: heavy overplotting in the band around no change, a cloud whose spread changes with expression and is often widest at low expression, a smoothing curve lying almost on the reference line, far more gray points than colored ones, and significant genes inside the fold-change lines.
