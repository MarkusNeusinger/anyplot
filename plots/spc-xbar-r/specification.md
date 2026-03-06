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
- `ucl` (float) - Upper Control Limit (process mean + 3 sigma)
- `lcl` (float) - Lower Control Limit (process mean - 3 sigma)
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
