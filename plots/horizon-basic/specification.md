# horizon-basic: Horizon Chart

## Description

A horizon chart displays many time series compactly by folding values into color-coded bands, preserving local resolution while minimizing vertical space. It divides the y-axis into bands and uses color intensity to encode magnitude, allowing dozens of series to be compared in limited space. This technique is particularly effective when monitoring many metrics simultaneously where traditional line charts would become unreadable.

## Applications

- Dashboard monitoring displaying 50+ system metrics (CPU, memory, network) in a compact panel
- Stock market sector analysis comparing performance of multiple securities over time
- Environmental monitoring showing temperature, humidity, and other readings from multiple sensors

## Data

- `date` (datetime) - Time points for the x-axis, typically evenly spaced
- `value` (numeric) - The measured value at each time point
- `series` (categorical) - Identifier for each time series when displaying multiple
- Size: 100-1000 time points per series, 5-50 series for effective comparison
- Example: Server metrics over 24 hours, stock prices over trading days

## Notes

- Typically uses 2-4 bands with mirrored positive/negative coloring (e.g., blue for positive, red for negative)
- Color intensity increases with magnitude within each band
- Baseline should be meaningful (often zero or mean value)
- Works best with normalized or similarly-scaled data across series

## What a good version looks like

- A good version shows: one compact row per series, the rows stacked on a shared time axis and each labeled with its series name, so many series compare at a glance in little vertical space.
- A good version shows: each row's values folded into bands of equal value range layered on the row's baseline, a higher band drawn over the lower ones in a more intense color, so a darker fill always means a larger magnitude.
- A good version shows: values below the baseline in a second hue, mirrored into the same row as the Notes describe (such as blue for positive and red for negative), with both hues and every intensity step distinguishable in both themes.
- A good version shows: the same baseline meaning, band ranges and color steps in every row, so a color stands for the same magnitude and sign across all series.
- A good version shows: the basic variant's folded bands, one row per series: besides the bands and row labels, no line overlay of the unfolded series, reference or mean lines, highlighted rows or time spans, or callouts and event annotations.
- Expected, not a defect: abrupt color steps where a series crosses into the next band, peaks cut flat at the top of a row and continued in a darker band, quiet rows that show only the palest band, and rows without their own value axis.
