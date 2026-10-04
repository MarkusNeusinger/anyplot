# forest-basic: Meta-Analysis Forest Plot

## Description

A forest plot displays effect sizes with confidence intervals from multiple studies in a meta-analysis. Each study is represented as a point estimate with horizontal whiskers showing the confidence interval, and a diamond at the bottom shows the pooled estimate. The plot includes a vertical reference line at the null effect (typically 0 or 1), making it easy to assess statistical significance and heterogeneity across studies.

## Applications

- Summarizing results from systematic reviews in medical research
- Comparing treatment effects across multiple clinical trials
- Visualizing heterogeneity and consistency of findings across studies
- Presenting pooled effect estimates with confidence intervals

## Data

- `study` (str) - Study name or identifier
- `effect_size` (float) - Point estimate of the effect (e.g., odds ratio, risk ratio, mean difference)
- `ci_lower` (float) - Lower bound of the confidence interval
- `ci_upper` (float) - Upper bound of the confidence interval
- `weight` (float, optional) - Study weight for visual sizing of markers
- Size: 5-30 studies
- Example: Meta-analysis of randomized controlled trials comparing treatment vs control

## Notes

- Diamond shape for the pooled/overall estimate at the bottom, computed from the studies (e.g., inverse-variance weights)
- Vertical reference line at null effect (0 for mean difference, 1 for ratios)
- Marker size proportional to study weight when provided
- Studies typically ordered by effect size or chronologically
- Clear axis labels showing the effect measure and scale

## What a good version looks like

- A good version shows: one row per study, named at its row, with a marker at its effect size and a horizontal line through it from the lower to the upper confidence bound, in a meaningful order, typically by effect size or chronological as the Notes suggest, and no marker moved off its value.
- A good version shows: the pooled estimate as a diamond in its own row at the bottom, below every study, as the Notes ask, centered on the pooled estimate with its left and right tips at the pooled interval's bounds, and set apart from the study markers.
- A good version shows: a vertical reference line at the null effect, as the Notes ask (0 for a mean difference, 1 for a ratio), running through all study rows and the diamond's row, on an axis labeled with the effect measure and its scale.
- A good version shows: study markers whose size is proportional to study weight where weights are provided, as the Notes ask, with the smallest marker still visible and the largest kept within its own row.
- A good version shows: the basic variant's single meta-analysis: the study rows, the pooled diamond and the null line, besides the weight-sized markers the Notes ask for, and no subgroups with their own diamonds, further reference lines, trend lines, highlighted studies or bands, or callouts.
- Expected, not a defect: intervals of very different width, wide intervals on the lightest studies, a heavy study's marker that covers most of its own narrow interval, intervals that cross the null line, studies on both sides of it, and a pooled diamond far narrower than any study's interval.
