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
