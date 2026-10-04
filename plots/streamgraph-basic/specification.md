# streamgraph-basic: Basic Stream Graph

## Description

A streamgraph (also known as a stacked area chart with a centered baseline) displaying the composition of multiple categories over time with smooth, flowing curves. Unlike traditional stacked area charts, streamgraphs use a baseline centered around the x-axis, creating an organic, river-like appearance that emphasizes the overall shape and relative proportions of each category while minimizing the visual distortion of individual layers.

## Applications

- Music listening trends showing genre popularity over months
- Topic popularity evolution in social media or news
- Market share changes among competitors over time
- Resource allocation across teams or projects over quarters

## Data

- `time` (datetime/numeric) - continuous time axis for the x-dimension
- `category` (categorical) - distinct categories/series to stack
- `value` (numeric) - magnitude for each category at each time point
- Size: 10-100 time points with 3-8 categories
- Example: monthly streaming hours by music genre over two years

## Notes

- Use smooth interpolation (spline/basis) for flowing curves
- Center the stack around a horizontal middle axis, with a symmetric (silhouette) or wiggle-minimizing baseline
- Use distinct, harmonious colors for each category
- Include a legend to identify categories
- Consider color palette that works well for adjacent areas

## What a good version looks like

- A good version shows: each category as a filled layer lying directly on the next with no gaps between layers, so a layer's thickness at any time is its value and its vertical position carries no value.
- A good version shows: the stack centered on a horizontal middle axis, as the Notes ask, either mirrored symmetrically or offset to minimize wiggle, never rising from a flat baseline.
- A good version shows: smooth, flowing layer edges, as the Notes ask, with each layer's thickness at a time point still its value there; the smoothing shapes the curve between time points, not the data.
- A good version shows: one distinct color per category, the same along the whole stream and named in a legend, as the Notes ask, with neighboring layers distinguishable in both themes.
- A good version shows: the basic variant's single centered stream and its legend: no total or trend line, reference or mean lines, highlighted layers or bands, callouts or event annotations, and no split into separate streams.
- Expected, not a defect: upper and lower outlines that both wiggle, layers pushed up and down by their neighbors, layers that pinch to almost nothing, and a vertical axis without value ticks, because only thickness is read.
