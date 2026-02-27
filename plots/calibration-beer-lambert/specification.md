# calibration-beer-lambert: Beer-Lambert Calibration Curve

## Description

A calibration curve plotting absorbance versus concentration following Beer-Lambert law (A = εlc). Measured calibration standards are shown as scatter points with a linear regression fit line. The regression equation (y = mx + b) and R² value are displayed on the plot. An example unknown sample is marked with dashed lines extending to both axes, demonstrating how the curve is used to determine concentration from a measured absorbance. This plot is fundamental in analytical chemistry for quantitative spectrophotometric analysis.

## Applications

- Determining unknown sample concentrations from UV-Vis spectrophotometry measurements in research laboratories
- Quality control in pharmaceutical analysis to verify drug substance concentrations meet specifications
- Environmental water quality testing for contaminant levels using colorimetric assays
- Clinical chemistry laboratory measurements for blood analyte quantification

## Data

- `concentration` (numeric) - Standard concentrations in mol/L or mg/L (independent variable, x-axis)
- `absorbance` (numeric) - Measured absorbance values at a specific wavelength (dimensionless, y-axis)
- Size: 5-10 calibration standards including a blank (zero concentration)
- Example: A set of standard solutions at known concentrations measured on a UV-Vis spectrophotometer at a fixed wavelength

## Notes

- Display the linear regression equation (y = mx + b) and R² value as text annotation on the plot
- Include a prediction interval band around the regression line
- Mark one example "unknown" sample point with dashed horizontal and vertical lines extending to both axes to illustrate concentration determination
- X-axis label should include units (e.g., "Concentration (mg/L)")
- Y-axis label should be "Absorbance" (dimensionless)
- Data should follow a linear relationship consistent with Beer-Lambert law over the concentration range used
