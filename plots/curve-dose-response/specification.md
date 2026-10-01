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

## What a good version looks like

- A good version shows: response against concentration on a logarithmic x axis, as the Notes require, with each compound's fitted 4PL curve a smooth sigmoid running from one plateau to the other and the compounds told apart by a legend, as the Notes ask.
- A good version shows: the measured data points at their concentration and response values with SEM error bars, overlaid on the fitted curve, as the Notes ask, each curve running through the scatter of its own points.
- A good version shows: EC50/IC50 marked with dashed horizontal and vertical reference lines that meet on the curve at its half-maximal response, as the Notes ask, which lies halfway between that curve's bottom and top plateau.
- A good version shows: horizontal dashed lines at the top and bottom asymptotes, as the Notes ask, at the levels where the fitted curve flattens and subordinate to the curves and points.
- A good version shows: a confidence band around at least one fitted curve, as the Notes ask, enclosing that curve between a lower and an upper bound and translucent enough that the curve, points and reference lines stay visible through it in both themes.
- Expected, not a defect: only a few points per compound, points scattering around the fit, curves shifted along the concentration axis or differing in steepness and plateau height, plateaus that stop short of the axis ends, and EC50 lines of two compounds lying close together.
