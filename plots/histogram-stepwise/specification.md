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
