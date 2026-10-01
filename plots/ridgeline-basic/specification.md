# ridgeline-basic: Basic Ridgeline Plot

## Description

A ridgeline plot (also known as Joy Plot, named after the Joy Division album cover) displays the distribution of multiple groups by stacking partially overlapping density curves vertically. This creates a mountain ridge appearance that allows efficient comparison of many distributions simultaneously while maintaining a compact and visually striking presentation.

## Applications

- Comparing temperature distributions across months to reveal seasonal patterns
- Analyzing survey response distributions by demographic segments
- Visualizing population age distributions across different regions or time periods
- Showing how performance metrics vary across different teams or time windows

## Data

- `value` (numeric) - The continuous variable to visualize as density curves
- `group` (categorical) - The grouping variable that creates separate ridges (5-20 groups recommended)
- Size: 50-500 observations per group for smooth density estimation
- Example: Monthly temperature readings, survey scores by age group, reaction times by condition

## Notes

- Stack density curves vertically with partial overlap (typically 50-70% overlap)
- Y-axis should display group labels rather than numeric values
- Consider color gradients or distinct colors to differentiate ridges
- Ensure sufficient overlap for visual cohesion while maintaining readability
- Order groups meaningfully (chronological, alphabetical, or by distribution characteristic)

## What a good version looks like

- A good version shows: one density curve per group over a shared horizontal value axis, each on its own baseline, with the baselines stacked at even spacing up the vertical axis.
- A good version shows: a vertical axis that carries the group labels, each at its ridge's baseline, rather than numeric density values, as the Notes ask.
- A good version shows: neighboring ridges that partially overlap, as the Notes ask, with each ridge's outline still traceable against the ridge behind it in both themes.
- A good version shows: groups in a meaningful order, as the Notes ask: chronological, alphabetical or by a distribution characteristic.
- A good version shows: the basic variant's ridges, in the color gradient or distinct colors the Notes allow, and besides the ridges no rug or points, histogram bars, quantile, mean or other reference lines, highlighted ridges or bands, or callouts.
- Expected, not a defect: ridges that cover the lower slopes of the ridge behind them, ridges of different height and width, skewed or two-peaked shapes, and no density scale, because only the shapes and positions are compared.
