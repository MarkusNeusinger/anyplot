# stem-basic: Basic Stem Plot

## Description

A stem plot displays data points as markers connected to a baseline by vertical lines (stems). Each data point is represented by a marker at the data value with a thin line extending down to a baseline, making it ideal for visualizing discrete or sequential data where individual values matter. This plot type is particularly useful in signal processing and scientific applications where the discrete nature of measurements needs emphasis.

## Applications

- Visualizing impulse responses and discrete-time signals in signal processing
- Displaying discrete probability distributions where individual probabilities need highlighting
- Showing time series with discrete events or measurements
- Scientific data visualization emphasizing individual measurement points

## Data

- `x` (numeric) - Position along horizontal axis (sequence index or time)
- `y` (numeric) - Value determining stem height from baseline
- Size: 10-100 data points for optimal clarity
- Example: Discrete signal samples, probability mass function values

## Notes

- Stems should be thin vertical lines from baseline (typically y=0) to data points
- Markers should be clearly visible circles at the top of each stem
- Baseline position at y=0 unless data requires different baseline
- Consistent marker size and stem width throughout the plot

## What a good version looks like

- A good version shows: one thin vertical stem per data point, running from the baseline to a circular marker at the data value, so stem length stays proportional to the value's distance from the baseline.
- A good version shows: the baseline at zero, or at another level only where the data requires it, as the Notes say, with every stem starting from that one level.
- A good version shows: one marker size and one stem width throughout, as the Notes ask, with the stems clearly thinner than the markers and both visible in both themes.
- A good version shows: the basic variant's single series: one color for all stems and markers, and no second series, connecting line or envelope curve through the markers, reference or mean lines besides the baseline, highlighted stems or bands, value-dependent color or size, or callouts.
- Expected, not a defect: stems of very different lengths, stems pointing down from the baseline for negative values, and a value near the baseline whose marker sits almost on it; they are the point of the chart, not an imbalance to fix.
