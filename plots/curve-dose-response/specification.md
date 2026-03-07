# curve-dose-response: Pharmacological Dose-Response Curve

## Description

A sigmoidal dose-response curve that plots biological response against drug concentration on a logarithmic x-axis, fitted using a four-parameter logistic (4PL) model. This visualization is essential for determining drug potency metrics such as EC50 (half-maximal effective concentration) or IC50 (half-maximal inhibitory concentration), Hill slope steepness, and upper/lower response asymptotes. It enables rapid visual comparison of compound efficacy and is a standard tool in pharmacological analysis.

## Applications

- Pharmacology: determining EC50/IC50 values to compare drug potency across compounds
- Toxicology: establishing dose-dependent toxicity thresholds and lethal dose estimates
- Drug discovery: screening and ranking candidate compounds by efficacy and Hill slope
- Environmental science: assessing pollutant concentration effects on biological organisms

## Data

- `concentration` (float) - Drug or compound concentration values (typically spanning several orders of magnitude)
- `response` (float) - Measured biological response (e.g., % inhibition, % activation, cell viability)
- `compound` (string) - Compound or treatment identifier for comparing multiple curves
- `response_sem` (float) - Standard error of the mean for each data point (for error bars)
- Size: 6-12 concentration points per compound, 1-3 compounds
- Example: Synthetic dose-response data for 2 compounds with concentrations from 1e-9 to 1e-4 M

## Notes

- X-axis must use a logarithmic scale (log10 of concentration)
- Fit a 4-parameter logistic (4PL) sigmoid: response = Bottom + (Top - Bottom) / (1 + (EC50/concentration)^HillSlope)
- Mark EC50/IC50 with dashed horizontal and vertical reference lines intersecting the curve at the half-maximal response
- Display data points with error bars (SEM) overlaid on the fitted curve
- Show horizontal dashed lines for top and bottom asymptotes
- Include at least 2 compounds/curves to demonstrate comparison capability
- Use a legend to distinguish compounds and include a confidence band (95% CI) around at least one fitted curve
