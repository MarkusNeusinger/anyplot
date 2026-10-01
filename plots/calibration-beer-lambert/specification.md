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

## What a good version looks like

- A good version shows: absorbance on the y axis against concentration on the x axis, the x label carrying its unit, as the Notes ask, with every calibration standard, the blank at zero concentration included, as a marker at its measured values.
- A good version shows: a straight regression line through the standards, with the regression equation and the R² value as text on the plot, as the Notes ask, the drawn line matching the slope and intercept the equation states.
- A good version shows: a prediction interval band around the regression line, as the Notes ask, drawn behind the line and the markers and visible as a band in both themes.
- A good version shows: one unknown sample marked on the regression line so it can be told apart from the standards, with dashed horizontal and vertical lines running from it to both axes, as the Notes ask, so the concentration read from its absorbance can be traced.
- Expected, not a defect: standards scattered slightly off the line, an intercept that is not exactly zero, a prediction band that is narrow because the fit is tight and widens toward the ends of the range, and an R² very close to its maximum.
