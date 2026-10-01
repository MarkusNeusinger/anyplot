# curve-oc: Operating Characteristic (OC) Curve

## Description

An Operating Characteristic (OC) curve shows the probability of accepting a lot as a function of the true fraction defective in that lot. It is the primary tool for evaluating and comparing acceptance sampling plans, revealing how well an inspection plan discriminates between good and bad lots. The S-shaped curve highlights producer's risk (rejecting good lots) and consumer's risk (accepting bad lots), making it essential for designing effective quality inspection strategies.

## Applications

- Quality inspection: designing and comparing single-sample acceptance sampling plans with different sample sizes and acceptance numbers
- Incoming goods inspection: evaluating whether a supplier's defect rate meets contractual AQL (Acceptable Quality Level) requirements
- Regulatory compliance: assessing inspection plans against standards such as MIL-STD-1916 or ISO 2859 for defense and commercial procurement
- Process improvement: visualizing how increasing sample size tightens the discrimination between acceptable and unacceptable lot quality

## Data

- `fraction_defective` (float) - true proportion of defective items in the lot, ranging from 0.0 to 1.0 (x-axis)
- `probability_acceptance` (float) - probability that the lot will be accepted under the sampling plan, ranging from 0.0 to 1.0 (y-axis)
- `sample_plan` (string) - label identifying the sampling plan, e.g., "n=50, c=2" (used for legend when plotting multiple curves)
- Size: 100-200 points per curve, 2-4 curves for comparison
- Example: binomial probability calculations for single-sample acceptance plans with varying sample sizes (n) and acceptance numbers (c)

## Notes

- Compute acceptance probabilities using the binomial cumulative distribution function: P(accept) = sum of C(n,k) * p^k * (1-p)^(n-k) for k = 0 to c
- Annotate AQL (Acceptable Quality Level) and LTPD (Lot Tolerance Percent Defective) on the x-axis with vertical reference lines or markers
- Mark producer's risk (alpha) at AQL and consumer's risk (beta) at LTPD with labeled points or shaded regions
- Plot at least two OC curves with different sampling plans (e.g., n=50 c=1 and n=100 c=2) to show the effect of sample size on discrimination power
- Use a smooth, continuous line style; the x-axis should range from 0 to a reasonable upper bound (e.g., 0.15 or 0.20) rather than the full 0-1 range for practical readability

## What a good version looks like

- A good version shows: at least two OC curves for different sampling plans, as the Notes ask, each named by its plan in a legend or direct label, differing enough in steepness or position that the effect of the plan on discrimination reads from the comparison.
- A good version shows: each curve as a smooth, continuous line, as the Notes ask, through its computed acceptance probabilities: starting at certain acceptance for a lot without defectives and never rising as the fraction defective grows.
- A good version shows: an x axis running from zero to a practical upper fraction defective instead of the full range, as the Notes ask, so the falling part of the curves fills the plot.
- A good version shows: AQL and LTPD annotated on the x axis with vertical reference lines or markers, as the Notes ask, each identified by name.
- A good version shows: the producer's risk at AQL and the consumer's risk at LTPD marked with labeled points or shaded regions, as the Notes ask, read off a curve at those quality levels: the producer's risk as the gap below certain acceptance, the consumer's risk as the curve's height.
- Expected, not a defect: curves that nearly coincide at the top left and cross further along, a flat shoulder before the fall, a long tail hugging zero, lines without markers at the computed points, and risk marks that refer to one of the plans only.
