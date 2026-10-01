# probability-weibull: Weibull Probability Plot for Reliability Analysis

## Description

A Weibull probability plot displays failure or lifetime data on Weibull probability paper (logarithmic x-axis for time/cycles, linearized Weibull CDF on y-axis) with a fitted straight line. It is the standard tool in reliability engineering for estimating Weibull distribution parameters (shape and scale), assessing whether data follow a Weibull distribution, and extrapolating failure probabilities. The slope of the fitted line gives the shape parameter (beta), while the characteristic life (eta) is read at the 63.2% failure probability crossing.

## Applications

- Predicting product warranty returns by fitting field-failure data and extrapolating to future time periods
- Comparing fatigue-life distributions of two material batches to determine which has higher reliability
- Estimating B10 life (time at which 10% of units fail) for bearing or component qualification testing

## Data

- `time_to_failure` (numeric) - observed failure or censoring time in hours, cycles, or miles
- `cumulative_probability` (numeric) - estimated cumulative failure probability for each data point (median rank or similar estimator)
- `is_censored` (boolean) - whether the observation is right-censored (suspended) rather than a true failure
- Size: 10-100 failure observations
- Example: turbine blade fatigue-life data with a mix of failures and suspensions

## Notes

- X-axis should use a logarithmic scale; y-axis should use a linearized Weibull scale (ln(-ln(1-F))) so that Weibull-distributed data plots as a straight line
- Display the fitted line with annotated shape parameter (beta) and scale parameter (eta)
- Use median rank approximation (i-0.3)/(n+0.4) for plotting positions
- Distinguish censored points visually (e.g., hollow markers vs filled markers for failures)
- Include a horizontal reference line at 63.2% cumulative probability (characteristic life)

## What a good version looks like

- A good version shows: a logarithmic time axis and a linearized Weibull probability axis, as the Notes ask, so that a Weibull model is a straight line across the plot.
- A good version shows: each failure as a point at its failure time and its plotting position, the median rank the Notes ask for, never jittered, displaced or smoothed.
- A good version shows: the fitted line drawn straight through the failures and annotated with the shape parameter beta and the scale parameter eta, as the Notes ask, the annotated values agreeing with the line.
- A good version shows: a horizontal reference line at the 63.2 percent cumulative probability, as the Notes ask, crossing the fitted line at the characteristic life eta.
- A good version shows: censored observations visually distinct from failures, as the Notes ask, for example hollow markers against filled ones, with the difference still readable in both themes.
- Expected, not a defect: points that wander around the fitted line, most at the earliest and latest failures, probability ticks unevenly spaced along the y axis, a fitted line that extends beyond the data, and censored points mixed in among the failures.
