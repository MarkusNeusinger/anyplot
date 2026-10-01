# psychrometric-basic: Psychrometric Chart for HVAC

## Description

A psychrometric chart plots dry-bulb temperature against humidity ratio, overlaid with curves for relative humidity, wet-bulb temperature, enthalpy, and specific volume. It is the fundamental tool for HVAC system design and air conditioning process analysis. The chart reveals the thermodynamic properties of moist air at a glance, enabling engineers to trace heating, cooling, humidification, and dehumidification processes as paths on the diagram.

## Applications

- HVAC engineering: designing and analyzing air conditioning systems by tracing process paths (heating, cooling, mixing) on the chart
- Building science: evaluating indoor thermal comfort zones and identifying condensation risks
- Industrial process engineering: optimizing drying operations and clean room environmental control

## Data

- `dry_bulb_temp` (float) - Dry-bulb air temperature in degrees Celsius, x-axis primary variable
- `humidity_ratio` (float) - Mass of water vapor per mass of dry air in g/kg, y-axis primary variable
- `relative_humidity` (float[]) - Constant relative humidity curves from 10% to 100% in 10% increments
- `wet_bulb_temp` (float[]) - Diagonal lines of constant wet-bulb temperature
- `enthalpy` (float[]) - Oblique lines of constant enthalpy in kJ/kg
- `specific_volume` (float[]) - Lines of constant specific volume in m3/kg
- Size: derived from psychrometric equations over a dry-bulb range of -10 to 50 degrees Celsius
- Example: standard atmosphere (101.325 kPa) psychrometric properties computed from ASHRAE formulas

## Notes

- The saturation curve (100% RH) forms the upper boundary of the chart and should be visually prominent
- Relative humidity curves (10%-100%) should be drawn as smooth curves between the saturation line and x-axis
- Wet-bulb and enthalpy lines run diagonally from upper-left to lower-right
- Specific volume lines run at a slightly different diagonal angle
- Include at least one example HVAC process path (e.g., cooling and dehumidification) shown as an arrow or highlighted line segment between two state points
- A comfort zone region (approximately 20-26 C, 30-60% RH) should be highlighted as a shaded rectangle or polygon
- All property lines should be labeled directly on the chart, not just in a legend
- Use standard sea-level atmospheric pressure (101.325 kPa) for calculations

## What a good version looks like

- A good version shows: dry-bulb temperature on the x axis and humidity ratio on the y axis, with the saturation curve as the visually prominent upper boundary and the relative humidity curves as smooth curves between it and the x-axis, as the Notes ask, none crossing another.
- A good version shows: wet-bulb and enthalpy lines running diagonally from upper left to lower right and specific volume lines at their own, different diagonal angle, as the Notes ask, the line families told apart by style or color in both themes.
- A good version shows: the property lines labeled directly on the chart with their values, as the Notes ask, not only in a legend, each label attached to the line it names.
- A good version shows: an example HVAC process path as an arrow or highlighted segment between two state points at their true coordinates, and the comfort zone as a shaded rectangle or polygon over its temperature and humidity range, as the Notes ask, both standing out from the property lines.
- A good version shows: the basic variant's standard chart at one pressure: besides the property-line families, their labels, the process path and the comfort zone the Notes ask for, no further reference lines, other highlighted regions, callouts beyond the state points and process, second chart or side panel.
- Expected, not a defect: a dense web of line families crossing one another, labels close together where the families converge toward the saturation curve, wet-bulb and enthalpy lines so nearly parallel that only their style separates them, lines cut off at the saturation curve, and an empty area above it.
