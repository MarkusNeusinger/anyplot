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
