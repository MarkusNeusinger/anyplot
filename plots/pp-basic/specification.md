# pp-basic: Probability-Probability (P-P) Plot

## Description

A diagnostic plot comparing the cumulative distribution function (CDF) of observed data against a theoretical distribution by plotting empirical CDF values against theoretical CDF values. Unlike Q-Q plots which compare quantiles, P-P plots compare cumulative probabilities on both axes (0 to 1), making them more sensitive to deviations in the center of the distribution. Points falling along the 45-degree diagonal indicate a good fit.

## Applications

- Assessing whether sample data follows a hypothesized distribution (e.g., normality testing for regression residuals)
- Reliability engineering: selecting the best-fit distribution for failure time data
- Quality control: verifying process measurements conform to expected distributional assumptions

## Data

- `observed` (numeric) - Sample data values drawn from an unknown distribution
- `theoretical_distribution` (string) - Name of the theoretical distribution to compare against (e.g., normal)
- Size: 50-500 data points
- Example: 200 samples from a slightly skewed distribution compared against a normal reference

## Notes

- Both axes range from 0 to 1 (cumulative probabilities)
- Include a 45-degree reference line representing perfect distributional fit
- Use a square aspect ratio to preserve the visual meaning of the diagonal
- Sort observed data and compute empirical CDF as i/(n+1) or similar plotting position formula
- Evaluate theoretical CDF using fitted or specified distribution parameters
- S-shaped deviations from the diagonal suggest the data has heavier or lighter tails than the reference distribution
- Optional: a pointwise confidence envelope around the reference line, drawn fainter than the points

## What a good version looks like

- A good version shows: one point per observation, pairing its empirical cumulative probability from the sorted data with the theoretical cumulative probability at the same value, as the Notes ask, every point at its computed values and never jittered or smoothed.
- A good version shows: both axes running from 0 to 1, as the Notes ask, in a square plot area, so that equal steps of probability are equally long on both axes.
- A good version shows: the 45-degree reference line of perfect fit, as the Notes ask, running from corner to corner of the unit square, distinct from the points and visible in both themes.
- A good version shows: the basic variant's one sample against one theoretical distribution: besides the diagonal the Notes ask for and the faint envelope they allow, no second sample or distribution, further reference lines, highlighted points or regions, callouts or statistic annotations, or marginal plots.
- Expected, not a defect: points that bow away from the diagonal or snake around it in an S shape, with the widest gaps in the middle of the range, while both ends close in on the corners without quite reaching them; the ends are held near the diagonal by construction and the departures are the plot's finding.
