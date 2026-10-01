# windbarb-basic: Wind Barb Plot for Meteorological Data

## Description

A wind barb plot displays wind speed and direction at specific locations using standard meteorological barb notation. Each barb consists of a staff pointing in the direction from which the wind blows, with short barbs (5 knots), long barbs (10 knots), and triangular pennants (50 knots) attached to indicate speed. This internationally recognized symbology enables rapid interpretation of wind patterns across weather maps and atmospheric data visualizations.

## Applications

- Displaying surface wind observations across weather station networks on synoptic maps
- Visualizing upper-air wind patterns from radiosonde or pilot balloon observations
- Showing wind field data from numerical weather prediction model output
- Presenting aviation weather information for flight planning and meteorological briefings

## Data

- `x` (numeric) - X-coordinate or longitude for barb position
- `y` (numeric) - Y-coordinate or latitude for barb position
- `u` (numeric) - Zonal (east-west) wind component in knots or m/s
- `v` (numeric) - Meridional (north-south) wind component in knots or m/s
- Size: 20-200 barbs recommended for clear visualization without overlap
- Example: Surface wind observations from a grid of weather stations

## Notes

- Wind barbs point in the direction FROM which the wind blows (opposite to arrow convention)
- Standard notation: half barb = 5 knots, full barb = 10 knots, pennant (triangle) = 50 knots
- Barbs are added on the left side of the staff in the Northern Hemisphere
- Calm winds (< 2.5 knots) shown as an open circle without a staff
- Grid spacing should prevent barb overlap for readability
- Consider using a map projection background for geographic data

## What a good version looks like

- A good version shows: one barb per observation with its staff anchored at the observation's x and y position and pointing toward the direction the wind blows from, as the Notes ask, the opposite of an arrow.
- A good version shows: speed in the standard notation the Notes give: half barbs, full barbs and filled triangular pennants whose values add up to the wind speed in knots, all drawn on one and the same side of the staff, as the Notes ask.
- A good version shows: calm winds, when the data has any, as an open circle alone, with the staff omitted, at the observation's position, as the Notes ask.
- A good version shows: barbs sized and spaced so that neighbors stay out of each other, as the Notes ask, with every half barb, full barb and pennant countable and visible in both themes.
- Expected, not a defect: staffs that point upwind and so look reversed to a reader used to arrows, light winds drawn with a single half barb, barbs turning from one observation to the next around a pressure center, and very different feather counts side by side.
- A good version shows: the basic variant's standard barb plot: besides the barbs, the calm circles the Notes ask for, the map background the Notes allow and a key that decodes the notation, no isobars or other overlaid field, reference or mean lines, highlighted barbs or regions, or callouts on pressure centers.
