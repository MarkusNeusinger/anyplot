# contour-map-geographic: Contour Lines on Geographic Map

## Description

A contour map overlays isolines (lines of equal value) onto a geographic basemap, visualizing continuous spatial data such as elevation, temperature, or atmospheric pressure across real-world coordinates. Unlike basic contour plots that use abstract x/y coordinates, this plot anchors contours to latitude/longitude positions with geographic context like coastlines, borders, or terrain. It combines the precision of isoline visualization with spatial awareness, making it ideal for meteorological, topographic, and environmental applications.

## Applications

- Topographic elevation maps showing terrain contours with labeled heights
- Weather maps displaying pressure systems (isobars) or temperature gradients (isotherms)
- Environmental monitoring showing pollution concentration or radiation levels across a region
- Oceanographic charts displaying water temperature or salinity isolines

## Data

- `lat` (numeric) - Latitude coordinates forming a regular grid (-90 to 90)
- `lon` (numeric) - Longitude coordinates forming a regular grid (-180 to 180)
- `value` (numeric) - Continuous variable at each grid point (elevation, temperature, pressure, etc.)
- Size: Grid of 20x20 to 100x100 points covering the geographic region of interest
- Example: Gridded elevation data, weather model output, or interpolated sensor measurements

## Notes

- Overlay smooth contour lines on a geographic basemap (coastlines, borders, or terrain)
- Label contour lines with values at appropriate intervals
- Support both line-only contours and optional filled contours between levels
- Use colormap appropriate to data type (terrain colors for elevation, temperature scales for weather)
- Include a colorbar legend showing the value range
- Ensure contour intervals are meaningful for the data (e.g., 100m for elevation, 4mb for pressure)

## What a good version looks like

- A good version shows: smooth isolines that trace equal values of the gridded field at their latitude and longitude, overlaid on a basemap of coastlines, borders or terrain that stays legible beneath them, as the Notes ask.
- A good version shows: contour levels at an interval that is meaningful for the data, as the Notes ask: round values in the variable's unit, evenly stepped unless the variable's range calls for another spacing.
- A good version shows: value labels on the contour lines at appropriate intervals, as the Notes ask, set along their lines and readable against the basemap, thinned where lines crowd.
- A good version shows: filled bands between levels, if drawn as the Notes allow, that match the line levels and leave the basemap readable; a line-only version is equally valid.
- A good version shows: a colormap appropriate to the data type and a color bar legend showing the value range, as the Notes ask, naming the variable and its unit.
- Expected, not a defect: closed loops around highs and lows, lines bunching where the field changes steeply and spreading where it is flat, lines that run off the map edge, and lines crossing coastlines and borders, which the field ignores.
