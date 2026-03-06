# histogram-capability: Process Capability Plot with Specification Limits

## Description

A process capability plot displays a histogram of measured process data overlaid with a fitted normal distribution curve and vertical lines for specification limits (LSL, USL) and target value. Capability indices (Cp, Cpk) are annotated on the plot to quantify how well the process meets specifications. This is a standard tool in quality engineering and Six Sigma for assessing whether a manufacturing or production process is capable of consistently producing output within tolerance.

## Applications

- Manufacturing quality control: evaluating whether machined part dimensions fall within engineering tolerances
- Pharmaceutical batch release: verifying that tablet weights or active ingredient concentrations meet regulatory specifications
- Six Sigma process improvement: measuring baseline process performance (Cp/Cpk) before and after optimization
- Semiconductor fabrication: assessing wafer thickness uniformity against specification limits

## Data

- `measurement` (numeric) - individual process measurements (e.g., part dimensions, weights, concentrations)
- `lsl` (numeric) - Lower Specification Limit, a single constant value
- `usl` (numeric) - Upper Specification Limit, a single constant value
- `target` (numeric) - target/nominal value, typically the midpoint of LSL and USL
- Size: 50-500 measurements recommended for meaningful capability analysis
- Example: 200 measurements of shaft diameter (mm) with LSL=9.95, USL=10.05, target=10.00

## Notes

- Cp and Cpk should be calculated from the data: Cp = (USL - LSL) / (6 * sigma), Cpk = min((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))
- The normal distribution curve should be fitted using the sample mean and standard deviation
- LSL and USL lines should be visually distinct (e.g., red dashed) from the target line (e.g., green dashed)
- Cp and Cpk values should be displayed as text annotations on the plot
- Generate synthetic measurement data using a normal distribution centered near the target value
