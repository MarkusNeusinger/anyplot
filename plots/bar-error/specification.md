# bar-error: Bar Chart with Error Bars

## Description

A bar chart with error bars displays categorical data as rectangular bars with vertical (or horizontal) lines extending from each bar to indicate uncertainty or variability. Error bars typically represent standard deviation, standard error, confidence intervals, or min/max ranges. This visualization is essential for comparing group means while communicating the reliability and precision of each measurement.

## Applications

- Scientific experiments comparing treatment groups with measurement uncertainty
- Survey results displaying response means with confidence intervals
- A/B test results showing conversion rates with statistical bounds
- Comparing group means with standard deviations across categories

## Data

- `category` (categorical) - Names or labels for each bar
- `value` (numeric) - Central value for each bar (mean, median, or measured value)
- `error` (numeric) - Error magnitude for symmetric error bars, or pair for asymmetric errors (lower, upper)
- Size: 3-12 categories for optimal readability

## Notes

- Error bars should have visible caps (horizontal lines at ends) to clearly mark the error range
- Include a legend or annotation explaining what the error bars represent (e.g., "±1 SD", "95% CI")
- Consider horizontal orientation when category labels are long or numerous
- Use consistent bar widths and error bar styling across all categories
- Asymmetric error bars may be needed for skewed distributions or percentage data

## What a good version looks like

- A good version shows: one bar per category extending from a zero baseline to its central value, so bar length stays proportional to the value, on a value axis that is never truncated and spans every error bar in full.
- A good version shows: an error bar on every bar, drawn through the bar end from the lower to the upper bound (with unequal arms where the errors are asymmetric), with visible caps at both ends, in one styling that stands out against the bars and the page in both themes.
- A good version shows: a legend or annotation naming what the error bars represent, such as a standard deviation, a standard error or a confidence interval.
- A good version shows: bars of one width with even gaps, and categories in a meaningful order: by value, or their natural order (a control group first, time points) when they have one, with horizontal bars and error bars when category labels are long.
- Expected, not a defect: error bars of very different lengths, ranges of neighboring bars that overlap, and asymmetric error bars on skewed or percentage data; they carry the uncertainty the chart exists to show.
