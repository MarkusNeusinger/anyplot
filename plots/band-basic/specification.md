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
- Boundaries and center line pass through every data value, with straight or monotone-interpolated segments; no fitted smoothing
- Consider showing the data generation equation or uncertainty source in the title

## What a good version looks like

- A good version shows: a filled region whose lower edge follows the lower boundary values and whose upper edge follows the upper boundary values at every x, with nothing filled outside the two boundaries.
- A good version shows: a semi-transparent fill, as the Notes ask, so gridlines and any overlapping element stay visible through the band in both themes, while the band stays distinct from the page.
- A good version shows: the central line, where the data has a central value, drawn on top of the band at its values, in a color or style that contrasts with the fill, as the Notes ask.
- A good version shows: boundaries and central line passing through every data value with straight or monotone-interpolated segments, as the Notes ask, rather than fitted smoothing, steps or separate blocks.
- A good version shows: the basic variant's one band and its central line, and no second band or nested interval, trend line besides the central line, reference or mean lines besides it, highlighted regions or points, or callouts.
- Expected, not a defect: a band whose width changes along x, including one that widens steadily toward the end of a forecast, a band that is not symmetric about the central line, and boundaries that wiggle like real data.
