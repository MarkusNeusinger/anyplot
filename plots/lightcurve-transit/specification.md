# lightcurve-transit: Astronomical Light Curve

## Description

A time-series plot showing the brightness of an astronomical object over time, designed to reveal exoplanet transit events as characteristic dips in flux. The plot displays photometric measurements with error bars against time or orbital phase, with an optional fitted transit model overlay. This visualization is fundamental in observational astronomy for detecting and characterizing planetary transits, variable stars, and other periodic brightness variations.

## Applications

- Detecting exoplanet transits in Kepler/TESS photometric survey data by identifying periodic flux dips
- Classifying variable stars (Cepheids, eclipsing binaries) through phase-folded brightness patterns
- Monitoring supernova brightness evolution over weeks to months for distance calibration

## Data

- `time` (float) - Observation time in days (e.g., BJD - 2457000 or phase 0.0-1.0)
- `flux` (float) - Normalized brightness/flux relative to baseline (e.g., 0.99-1.01)
- `flux_err` (float) - Measurement uncertainty for each flux value
- `model_flux` (float) - Best-fit transit model prediction at each time point
- Size: 200-1000 data points covering multiple transit events or one phase-folded period
- Example: Simulated exoplanet transit with ~1% depth, quadratic limb-darkened model

## Notes

- Y-axis should show relative flux (not magnitude) with the transit dip going downward
- Error bars on each data point are essential for conveying measurement precision
- Include a smooth model curve overlaid on the scatter data to show the fitted transit shape
- Data should be phase-folded (time mapped to orbital phase 0.0-1.0) to stack multiple transits
- Use a clean, minimal style appropriate for scientific publication
