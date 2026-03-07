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
