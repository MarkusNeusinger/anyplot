# line-arrhenius: Arrhenius Plot for Reaction Kinetics

## Description

An Arrhenius plot displays ln(k) versus 1/T to determine the activation energy of a chemical reaction from experimental rate constant data. The Arrhenius equation predicts a linear relationship on this transformed scale, where the slope equals -Ea/R (activation energy divided by the gas constant). This visualization is fundamental in physical chemistry and chemical engineering for characterizing reaction kinetics and comparing catalytic performance.

## Applications

- Determining activation energy of chemical reactions from experimental rate constant measurements at various temperatures
- Comparing reaction mechanisms and catalytic efficiency across different catalysts or reaction conditions
- Predicting reaction rates at untested temperatures by extrapolation of the fitted line
- Estimating shelf life of pharmaceutical products through accelerated stability studies

## Data

- `temperature_K` (numeric) — reaction temperature in Kelvin
- `rate_constant_k` (numeric) — experimentally measured rate constant at each temperature
- Size: 5-20 data points (typical experimental range covering a meaningful temperature span)
- Example: rate constants measured at 5 temperatures spanning 300-600 K for a first-order decomposition reaction

## Notes

- X-axis: 1/T (inverse temperature in K⁻¹), Y-axis: ln(k) (natural log of rate constant)
- Include a linear regression line through the data points with the R² value displayed
- Annotate the slope with an Ea/R label showing the extracted activation energy
- Show original temperature values (in K) as secondary x-axis tick labels for reference
- Data points should be clearly visible markers on top of the regression line

## What a good version looks like

- A good version shows: the natural log of the rate constant on the y axis against inverse temperature on the x axis, as the Notes ask, with every measured point at its own inverse temperature and log rate constant, never spaced evenly for looks.
- A good version shows: a straight regression line through the points with its R² value displayed, as the Notes ask, falling as inverse temperature rises, with the data markers drawn on top of the line and visible in both themes.
- A good version shows: an annotation at the line that ties its slope to -Ea/R, the sign the Description gives, and states the extracted activation energy, as the Notes ask.
- A good version shows: the original temperatures in K as secondary x-axis tick labels, as the Notes ask, each at the inverse-temperature position it corresponds to, so they decrease as inverse temperature increases.
- Expected, not a defect: points scattered slightly off the line, temperature labels that are unevenly spaced and run opposite to the inverse-temperature axis, negative values on the log axis, and points bunched toward one end when the temperatures were evenly spaced in K.
