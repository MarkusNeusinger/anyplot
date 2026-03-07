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
