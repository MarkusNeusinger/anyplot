# density-rug: Density Plot with Rug Marks

## Description

A kernel density estimation (KDE) plot combined with rug marks along the x-axis, showing both the smoothed probability distribution and the exact location of each individual data point. This combination provides the best of both worlds: the KDE reveals the overall shape, modality, and smoothed density of the distribution, while the rug marks preserve transparency about where actual observations fall, highlighting data density and potential gaps.

## Applications

- Exploratory data analysis where understanding both distribution shape and raw data placement matters
- Comparing sample distributions while maintaining visibility of actual observation counts and clustering
- Quality control analysis to identify process variations alongside individual measurement locations
- Academic and research presentations requiring both statistical summaries and data transparency

## Data

- `values` (numeric) - The continuous variable to visualize
- Size: 30-500 observations recommended (rug marks become cluttered with very large samples)
- Example: Response times, measurement errors, test scores, or any continuous variable

## Notes

- Display the KDE curve with fill for visual weight and the rug marks as small tick marks along the x-axis
- Use semi-transparent fill under the density curve to avoid obscuring the rug
- Rug marks should be subtle but visible, with slight transparency for overlapping points
- Consider jittering rug marks vertically if using thick ticks to reduce overplotting

## What a good version looks like

- A good version shows: a smooth density curve on a density axis that starts at zero, with a semi-transparent fill beneath it, as the Notes ask, so the rug and the gridlines stay visible through the fill.
- A good version shows: one small tick per observation along the x axis, each at its exact value, as the Notes ask, sitting at the foot of the curve and far shorter than it.
- A good version shows: rug marks that are subtle but visible in both themes, slightly transparent, as the Notes ask, so overlapping observations read darker.
- A good version shows: vertical jitter, if applied to thick ticks as the Notes allow, changing only a tick's vertical placement; every tick keeps its position on the value axis.
- A good version shows: a curve that agrees with the rug: it is high where ticks crowd and low across gaps, with tails that end near the outermost ticks.
- Expected, not a defect: ticks that merge into dense bands in clusters, bare gaps, isolated ticks in the tails, a curve that reaches slightly past the outermost ticks, and a skewed or two-peaked shape.
