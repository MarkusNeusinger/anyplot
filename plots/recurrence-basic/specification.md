# recurrence-basic: Recurrence Plot for Nonlinear Time Series

## Description

A recurrence plot is a binary or distance-based matrix visualization that reveals when states in a dynamical system recur over time. Both axes represent time indices, and a point is plotted at position (i, j) when the system state at time i is sufficiently similar to the state at time j (distance below a threshold). The resulting symmetric matrix exposes hidden structure in complex, nonlinear dynamics — diagonal lines indicate determinism, vertical/horizontal lines reveal laminar states, and block structures signal regime changes.

## Applications

- Nonlinear dynamics research: detecting transitions between chaotic and periodic behavior in simulated or observed dynamical systems
- Climate science: identifying regime shifts and recurring patterns in paleoclimate proxy records
- Cardiology: analyzing heart rate variability recurrence structure to distinguish healthy from pathological rhythms
- Financial engineering: detecting recurring volatility regimes and structural breaks in asset return series
- Mechanical engineering: fault detection in rotating machinery through vibration signal recurrence analysis

## Data

- `time` (numeric) - time index or timestamp for each observation
- `value` (numeric) - measured state variable of the dynamical system (e.g., displacement, voltage, price)
- `threshold` (numeric, parameter) - distance threshold epsilon below which two states are considered recurrent
- Size: 200-1000 time steps recommended for clear visual patterns
- Example: Lorenz attractor x-component sampled at regular intervals, or logistic map iterates near the onset of chaos

## Notes

- The main diagonal is always filled (every state recurs with itself) and should be visually present
- Use Euclidean distance in the embedding space to compute the distance matrix; apply a binary threshold for the standard recurrence plot
- Consider embedding the scalar time series using time-delay embedding (Takens' theorem) with appropriate embedding dimension and delay before computing distances
- A color-mapped variant showing continuous distances (instead of binary) is acceptable as an enhancement
- The plot should be square with equal axis scales, and axes labeled as time indices
- Typical visual encoding: dark points on light background for recurrent pairs, or a blue-to-white color scale for distance-based variant

## What a good version looks like

- A good version shows: a square plot with time indices on both axes at equal scales, as the Notes ask, and, in the standard thresholded form, a mark at every pair of times whose states are closer than the threshold.
- A good version shows: the main diagonal filled along its whole length, as the Notes ask, and the pattern mirrored across it.
- A good version shows: recurrent pairs in a tone that contrasts with the background in both themes, at a threshold and resolution where line structures and blocks can be told apart instead of a nearly full or nearly empty matrix.
- A good version shows: for the distance-based variant the Notes allow, a continuous color scale explained by a color bar that names the distance, with the smallest distances along the main diagonal.
- A good version shows: the basic variant's single recurrence matrix: besides the main diagonal and the continuous distance coloring the Notes allow, no reference or threshold lines, highlighted regions or bands, callouts on structures, time-series panel alongside, or recurrence statistics.
- Expected, not a defect: short diagonal line segments, isolated points, empty bands and corners, and block or checkerboard textures; they are the dynamics the plot exists to show, not noise to clean up.
