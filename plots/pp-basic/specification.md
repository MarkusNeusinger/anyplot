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
