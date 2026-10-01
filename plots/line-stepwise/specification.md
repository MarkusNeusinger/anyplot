# line-stepwise: Step Line Plot

## Description

A step function plot where values remain constant until the next change, creating horizontal-then-vertical transitions. This visualization emphasizes discrete changes rather than interpolated values.

## Applications

- Discrete state changes over time
- Price/value stepping (stock prices at close)
- Cumulative counts that increase discretely
- Digital signals and binary states
- Piecewise constant functions

## Data

- `x` (numeric) — Time or independent variable; can be continuous or discrete
- `y` (numeric) — Values that change at specific points
- Size: 50-500 points (depending on temporal frequency)
- Example:
```
x    | y
-----|-------
0    | 100
1    | 100
2    | 150
3    | 150
4    | 125
```

## Notes

- Step alignment options: 'pre' (before), 'mid' (middle), 'post' (after)
- Clear distinction from smooth line interpolation
- Horizontal segments show value persistence
- Vertical segments show instantaneous changes

## What a good version looks like

- A good version shows: the series drawn only as horizontal and vertical segments: each value held flat until the next change and each change drawn as a vertical jump, with no sloped or curved connections.
- A good version shows: one step alignment relative to the data points for the whole series (pre, mid or post, the options the Notes list), so the jumps fall on the data's x values, or halfway between them for mid, and every flat segment sits at its exact y value.
- A good version shows: a staircase that stays legible: where a value persists over several points, its plateau reads as one flat segment rather than a comb of vertical strokes.
- A good version shows: markers, if drawn, on the data points and small enough that the flat segments still read as lines.
- Expected, not a defect: jumps of very different height, plateaus of very different length, runs of repeated values that form one long flat segment, and the sharp corners themselves; none of them is to be smoothed.
