# phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)

## Description

A pressure-temperature (P-T) phase diagram showing the boundaries between solid, liquid, and gas phases of a substance. The diagram includes the triple point where all three phases coexist and the critical point beyond which the liquid-gas distinction vanishes. This is one of the most fundamental diagrams in chemistry and physics, essential for understanding phase transitions and states of matter.

## Applications

- Teaching phase transitions and states of matter in chemistry and physics courses
- Engineering process design requiring knowledge of substance phase behavior at given conditions
- Materials science research studying melting, boiling, and sublimation conditions

## Data

- `temperature` (numeric) - Temperature values along phase boundary curves (e.g., in Kelvin)
- `pressure` (numeric) - Pressure values along phase boundary curves (e.g., in atm or Pa)
- `phase_boundary` (categorical) - Identifies which boundary the point belongs to: solid-liquid, liquid-gas, or solid-gas
- `triple_point` (numeric pair) - Temperature and pressure coordinates of the triple point
- `critical_point` (numeric pair) - Temperature and pressure coordinates of the critical point
- Size: 50-200 points per boundary curve
- Example: Water phase diagram with triple point at 273.16 K / 611.73 Pa and critical point at 647.1 K / 22.064 MPa

## Notes

- Phase regions (solid, liquid, gas) should be clearly labeled in their respective areas
- The triple point and critical point should be marked with distinct markers and annotated
- The liquid-gas boundary terminates at the critical point; beyond it lies the supercritical fluid region
- A logarithmic pressure axis is common to accommodate the wide range of pressures
- Use representative data (e.g., water or CO2) rather than purely synthetic curves for realism
- The solid-liquid boundary is nearly vertical for most substances (positive slope); water is a notable exception with a negative slope

## What a good version looks like

- A good version shows: pressure on the y axis against temperature on the x axis, with the solid-liquid, liquid-gas and solid-gas boundary curves drawn through their data and meeting at the triple point; a logarithmic pressure axis, if used, has ticks that show it.
- A good version shows: the triple point and the critical point marked with distinct markers at their temperature and pressure coordinates and annotated, as the Notes ask.
- A good version shows: the liquid-gas boundary ending at the critical point, as the Notes say, never drawn on past it, and the supercritical fluid region, where it is labeled or shaded, lying beyond that point.
- A good version shows: the solid, liquid and gas regions each labeled inside its own area, as the Notes ask, solid on the cold, high-pressure side, gas on the hot, low-pressure side and liquid between the two boundaries above the triple point.
- A good version shows: a solid-liquid boundary that rises steeply from the triple point with the slope of the substance shown, as the Notes say: leaning toward lower temperature for water, toward higher temperature for most other substances.
- Expected, not a defect: a solid-liquid line that looks almost vertical, curves squeezed toward one edge on a linear pressure axis or flattened on a logarithmic one, regions of very unequal size, and a triple point close to an axis; they follow from the substance's real values.
