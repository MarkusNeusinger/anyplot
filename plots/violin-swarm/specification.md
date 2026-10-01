# violin-swarm: Violin Plot with Overlaid Swarm Points

## Description

A violin plot with individual data points overlaid as a swarm plot, combining smooth kernel density estimation with raw data visibility. The violin shape shows the distribution density while the swarm points reveal actual observations, enabling viewers to see both the overall distribution pattern and individual data values simultaneously. This hybrid approach provides maximum transparency, showing exactly how many observations exist at each level while maintaining the smooth distribution visualization.

## Applications

- Comparing gene expression levels across treatment conditions in biological research
- Analyzing response time distributions across experimental groups while showing individual trials
- Visualizing patient biomarker values across clinical groups with full data transparency
- Presenting survey response distributions where sample sizes vary between groups

## Data

- `category` (categorical) - Group labels for comparison on the categorical axis
- `value` (numeric) - Continuous variable values shown on the value axis
- Size: 20-200 observations per category, 2-5 categories
- Example: Reaction times (ms) across 4 experimental conditions with 50 observations each

## Notes

- Overlay swarm points on top of the violin, centered within the violin shape
- Use transparency on the violin (alpha 0.3-0.5) so swarm points remain visible
- Size swarm points appropriately to avoid excessive overlap while remaining visible
- Consider using a contrasting color for points vs violin fill
- Swarm points should spread horizontally to avoid overlap, staying within the violin boundary

## What a good version looks like

- A good version shows: a mirrored density shape for each category with that category's observations drawn on top of it as a swarm centered on the violin's axis, as the Notes ask.
- A good version shows: every swarm point at its value on the value axis, spread only across the category direction and staying inside the violin's outline, as the Notes ask.
- A good version shows: a translucent violin fill, as the Notes ask, so the swarm points stay visible on it in both themes.
- A good version shows: swarm points sized, as the Notes ask, to stay individually visible without hiding one another.
- A good version shows: one shared value axis for all violins that is not forced to zero, with each violin's tails ending near its data range instead of trailing far beyond it.
- Expected, not a defect: sideways swarm offsets, which are layout rather than data, points packed edge to edge in the densest value range, violin tips that reach past the outermost points, and widths and shapes that differ between categories, including multimodal or skewed ones.
