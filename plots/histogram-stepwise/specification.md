# histogram-stepwise: Step Histogram

## Description

A histogram displayed as step lines (outline only) without filled bars. The distribution is shown as connected horizontal and vertical line segments, creating a step function appearance.

## Applications

- Comparing multiple distributions without visual overlap
- Clean, minimal histogram visualization
- Overlaying distributions for direct comparison
- Print-friendly histogram representation

## Data

- `values` (numeric, continuous) — Raw continuous measurements to be binned and counted
- Size: 50–5000 points (larger datasets reveal distribution shape better)
- Example: Heights in cm, test scores, sensor readings

```
Value
------
12.5
18.3
15.7
22.1
24.6
19.2
...
```

## Notes

- No fill, only outline (step lines)
- Each bin represented by horizontal segment at count level
- Vertical segments connect adjacent bins
- Ideal for overlaying multiple distributions

## What a good version looks like

- A good version shows: the distribution as an outline only, as the Notes ask: a horizontal segment across each bin at its count, joined to its neighbors by vertical segments at the bin edges, with no filled bars.
- A good version shows: contiguous bins on a count axis that starts at zero, so the heights of the horizontal segments compare as counts.
- A good version shows: an outline strong enough to carry the plot without a fill, visible against the page and the gridlines in both themes.
- A good version shows: several distributions, if overlaid as the Notes allow, on shared bin edges, with outlines told apart by color or line style and named in a legend.
- Expected, not a defect: a jagged staircase with uneven neighboring steps, segments lying on the baseline across empty bins, and outlines that cross each other when overlaid; none of them is to be smoothed.
