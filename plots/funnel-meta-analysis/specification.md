# funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias

## Description

A funnel plot used in meta-analysis to assess publication bias by plotting individual study effect sizes against their precision (typically standard error). Studies scatter around a summary effect line, with pseudo 95% confidence limits forming an inverted funnel shape. In the absence of bias, studies distribute symmetrically around the summary effect; asymmetry suggests publication bias or systematic heterogeneity. This is a standard tool in systematic reviews and Cochrane-style meta-analyses.

## Applications

- Systematic review authors assessing whether small-study effects indicate publication bias across included trials
- Cochrane reviewers generating standard funnel plots as part of required reporting for intervention reviews
- Research methodologists evaluating selective reporting by visually inspecting funnel asymmetry
- Epidemiologists checking meta-analytic robustness before drawing pooled conclusions

## Data

- `effect_size` (float) - Point estimate from each study (e.g., odds ratio, mean difference, risk ratio)
- `std_error` (float) - Standard error of each study's effect estimate
- `study` (str, optional) - Study label or identifier for annotation
- Size: 8-30 studies
- Example: Meta-analysis of 15 randomized controlled trials comparing drug vs placebo, with log odds ratios and standard errors

## Notes

- Y-axis shows standard error (inverted so that larger/more precise studies appear at the top)
- X-axis shows the effect size measure
- Draw a vertical line at the summary/pooled effect size
- Draw pseudo 95% confidence limits as diagonal lines forming the funnel shape (summary effect +/- 1.96 * SE)
- Plot individual studies as points (optionally sized by weight or sample size)
- Include a vertical dashed reference line at the null effect (0 for differences, 1 for ratios) if different from summary effect
- Asymmetry in the scatter pattern suggests publication bias

## What a good version looks like

- A good version shows: one point per study at its effect size on the x axis and its standard error on the y axis, as the Notes ask, never jittered or displaced, with marker size, if it varies, growing with study weight or sample size as the Notes allow.
- A good version shows: the standard error axis inverted, as the Notes ask, so that the more precise studies sit at the top and the less precise ones spread out toward the bottom.
- A good version shows: a vertical line at the pooled effect and the pseudo confidence limits as two straight diagonal lines, as the Notes ask, closing in on the pooled effect toward the top and widening symmetrically about it toward the bottom, where their formula puts them.
- A good version shows: a dashed vertical reference line at the null effect when it differs from the pooled effect, as the Notes ask, distinguishable from the pooled-effect line.
- Expected, not a defect: studies outside the funnel limits, a lopsided scatter with one lower corner empty, few points near the top and a wider spread at the bottom, and a pooled effect away from the null; asymmetry is the finding the plot exists to show.
