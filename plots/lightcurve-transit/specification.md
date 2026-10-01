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

## What a good version looks like

- A good version shows: relative flux on the y axis, not magnitude, as the Notes ask, with a flat out-of-transit baseline at the normalized level and the transit as a dip going downward.
- A good version shows: the transits stacked by phase folding into one dip on an orbital phase axis, as the Notes ask, or, on the time axis in days the Data also allows, each transit as its own dip at its own time; every measurement sits at its own x value and flux.
- A good version shows: an error bar on each data point, as the Notes ask, light enough that the points and the dip stay visible through them.
- A good version shows: a smooth model curve drawn over the scatter, as the Notes ask, distinct from the points in both themes, flat outside the transit and following the dip from ingress through its bottom to egress.
- Expected, not a defect: a dip that is tiny against the flux level, scatter that is a good fraction of the transit depth, a dense band of overlapping points and error bars along the baseline, a transit that fills only a narrow slice of the phase axis, and a flux axis that does not start at zero.
