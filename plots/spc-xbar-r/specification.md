# spc-xbar-r: Statistical Process Control Chart (X-bar/R)

## Description

A Statistical Process Control (SPC) chart displaying sample means (X-bar) and ranges (R) plotted over time against control limits. The chart includes a center line representing the process mean, Upper Control Limit (UCL) and Lower Control Limit (LCL) at ±3 sigma, and optional warning limits at ±2 sigma. Out-of-control points are highlighted to signal process instability. This is a fundamental tool in manufacturing quality control and Six Sigma methodology for monitoring process stability.

## Applications

- Manufacturing quality control: monitoring dimensional measurements across production batches to detect process drift
- Healthcare process improvement: tracking patient wait times or lab turnaround times to identify systemic changes
- Service industry operations: monitoring call center response times or error rates to maintain service quality
- Software engineering: tracking build times or defect rates across releases to detect process degradation

## Data

- `sample_id` (integer) - Sequential sample number or time period identifier
- `sample_mean` (float) - Mean of measurements within each sample (X-bar values)
- `sample_range` (float) - Range of measurements within each sample (R values)
- `ucl` (float) - Upper Control Limit: X̄̄ + A2·R̄ on the X-bar chart, D4·R̄ on the R chart (3-sigma limits)
- `lcl` (float) - Lower Control Limit: X̄̄ − A2·R̄ on the X-bar chart, D3·R̄ on the R chart (0 for subgroups of 6 or fewer)
- `center_line` (float) - Process mean (X-bar-bar or R-bar)
- `upper_warning` (float) - Optional upper warning limit (+2 sigma)
- `lower_warning` (float) - Optional lower warning limit (-2 sigma)
- Size: 20-50 samples, each containing 4-5 individual measurements
- Example: Shaft diameter measurements taken in subgroups of 5 from a CNC machining process

## Notes

- Display X-bar chart on top and R chart on bottom as a vertically stacked pair sharing the same x-axis
- UCL and LCL lines should be dashed and clearly labeled
- Center line should be solid and distinct from data line
- Out-of-control points (beyond UCL/LCL) should be highlighted with a different color or marker
- Warning limits (±2 sigma) should be shown as lighter dashed lines if included
- Generate realistic synthetic data with at least 2-3 out-of-control points to demonstrate detection capability
- Use standard control chart constants (A2, D3, D4) for computing limits from sample data

## What a good version looks like

- A good version shows: the X-bar chart on top and the R chart below it, as the Notes ask, stacked on one shared sample axis so each sample lines up vertically across the two panels.
- A good version shows: in each panel, the sample values as points joined in sample order, every point at its own sample number and value.
- A good version shows: in each panel, a solid center line distinct from the data line, and dashed UCL and LCL lines running across all samples at their computed values, each labeled, as the Notes ask, and visible in both themes.
- A good version shows: every point beyond the UCL or LCL highlighted with a different color or marker, as the Notes ask, so the signals stand out from the in-control points.
- A good version shows: warning limits, if included, as lighter dashed lines between the center line and the control limits, subordinate to the control limits.
- Expected, not a defect: out-of-control points, shifts and runs on one side of the center line, a signal in one panel with none in the other, an R chart whose lower limit sits at zero on the axis floor with limits uneven about its center line, and panels on different y scales.
