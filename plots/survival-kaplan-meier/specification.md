# survival-kaplan-meier: Kaplan-Meier Survival Plot

## Description

A Kaplan-Meier survival plot visualizes the probability of survival (or event-free time) over a time period using a step function. It is the standard method for estimating survival functions from time-to-event data, handling censored observations where the event has not yet occurred. The plot shows how survival probability decreases over time, with optional confidence intervals and comparison between groups.

## Applications

- Medical research tracking patient survival rates after diagnosis or treatment
- Reliability engineering analyzing time-to-failure for equipment or components
- Customer analytics measuring time-to-churn or subscription retention
- Clinical trials comparing survival outcomes between treatment and control groups

## Data

- `time` (numeric) - Time to event or censoring (e.g., days, months, years)
- `event` (binary) - Event indicator (1 = event occurred, 0 = censored)
- `group` (categorical, optional) - Grouping variable for comparing survival curves
- Size: 50-1000 observations
- Example: Clinical trial data with patient survival times and treatment groups

## Notes

- Use step function (not smooth curves) to accurately represent discrete event times
- Include 95% confidence intervals as shaded bands around the survival curve
- Mark censored observations with tick marks on the curve
- When comparing groups, use distinct colors and include a legend
- Consider adding median survival time annotation and at-risk table below the plot
- Log-rank test p-value can be included when comparing groups

## What a good version looks like

- A good version shows: each survival curve as a step function, as the Notes ask, starting at full survival at time zero, flat between events and dropping vertically at the event times, never sloped, smoothed or rising.
- A good version shows: the confidence interval as a shaded band around each survival curve, as the Notes ask, stepping with its curve and translucent enough that the curves, and bands that overlap between groups, stay distinguishable in both themes.
- A good version shows: censored observations as tick marks on the curve, as the Notes ask, each at its censoring time and at the curve's height there, small enough not to be mistaken for a step.
- A good version shows: when groups are compared, one curve per group in distinct colors with a legend, as the Notes ask; a single curve without a group needs neither.
- A good version shows: the extras the Notes allow, if drawn, in their usual places: a median survival annotation where the curve crosses half survival, an at-risk table below the plot aligned with the time axis, and a log-rank p-value as text clear of the curves.
- Expected, not a defect: long flat steps, bigger drops and wider bands toward the right as fewer subjects remain at risk, a ragged tail, a curve that ends above zero because the last observations are censored, censoring ticks bunched late in follow-up, and curves that cross.
