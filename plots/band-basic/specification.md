# band-basic: Basic Band Plot

## Description

A band plot displays a filled region between two boundary lines, commonly used to show confidence intervals, prediction intervals, or ranges around a central trend line. The semi-transparent band provides visual representation of uncertainty or variability while maintaining visibility of underlying data or overlapping elements.

## Applications

- Displaying confidence intervals around regression lines in statistical analysis
- Showing forecast uncertainty ranges in time series predictions
- Visualizing min/max ranges or tolerance zones in manufacturing quality control
- Representing measurement uncertainty bands in scientific experiments

## Data

- `x` (numeric) - Independent variable, often representing time or sequence
- `y_lower` (numeric) - Lower boundary values defining the bottom of the band
- `y_upper` (numeric) - Upper boundary values defining the top of the band
- `y_center` (numeric) - Central trend line values (mean/median), shown as a contrasting line
- Size: 20-200 data points
- Example: Time series with 95% confidence interval bounds

## Notes

- Use semi-transparent fill (alpha 0.2-0.4) to allow visibility of overlapping elements
- Include a central line in a contrasting color/style when showing mean or median
- Ensure smooth interpolation between points for continuous data
- Consider showing the data generation equation or uncertainty source in the title
