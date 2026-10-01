# skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram

## Description

A Skew-T Log-P diagram is a specialized thermodynamic chart used in meteorology to display vertical atmospheric profiles. It features a logarithmic pressure axis (inverted, with surface at bottom) and temperature isotherms skewed 45 degrees to the right, allowing simultaneous visualization of temperature, dewpoint, and derived stability parameters. This diagram is essential for analyzing atmospheric soundings and assessing weather conditions.

## Applications

- Analyzing weather balloon (radiosonde) sounding data to understand atmospheric structure
- Assessing atmospheric stability and convective potential for severe weather forecasting
- Evaluating lifting condensation level, convective available potential energy (CAPE), and convective inhibition (CIN)
- Teaching meteorology students about thermodynamic processes in the atmosphere

## Data

- `pressure` (numeric) - Atmospheric pressure levels in hectopascals (hPa), typically ranging from 1000 hPa (surface) to 100 hPa (stratosphere)
- `temperature` (numeric) - Air temperature in degrees Celsius at each pressure level
- `dewpoint` (numeric) - Dewpoint temperature in degrees Celsius at each pressure level
- `wind_speed` (numeric, optional) - Wind speed in knots for wind barb display
- `wind_direction` (numeric, optional) - Wind direction in degrees (0-360) for wind barb display
- Size: 20-100 vertical levels (typical radiosonde resolution)
- Example: Standard atmospheric sounding with surface to upper troposphere coverage

## Notes

- Pressure axis must be logarithmic and inverted (1000 hPa at bottom, decreasing upward)
- Temperature isotherms should be drawn at 45-degree angle (skewed to the right)
- Include reference lines: dry adiabats (potential temperature), moist adiabats (equivalent potential temperature), and mixing ratio lines
- Temperature profile typically shown as solid line, dewpoint as dashed line
- Wind barbs along right edge are optional but enhance the diagram's utility
- Color coding can distinguish different reference line types for clarity

## What a good version looks like

- A good version shows: pressure on a logarithmic vertical axis with the surface at the bottom and pressure decreasing upward, as the Notes ask, so the isobars are horizontal lines that spread apart toward the top.
- A good version shows: straight isotherms skewed to the right at the 45-degree angle the Notes ask for, rising from lower left to upper right, with every level of the sounding at its own pressure and at its temperature read along those skewed isotherms.
- A good version shows: families of dry adiabats, moist adiabats and mixing ratio lines behind the sounding, as the Notes ask, each family told apart from the others and from the isotherms by color or line style, and all of them lighter than the two profiles.
- A good version shows: the temperature and dewpoint profiles as the two most prominent lines, told apart in both themes by line style or color (typically temperature solid and dewpoint dashed), with the dewpoint trace at or to the left of the temperature trace at every level.
- A good version shows: wind barbs, if drawn as the Notes allow, in a column along the right edge, each at its pressure level and clear of the profiles.
- Expected, not a defect: a dense web of crossing reference lines, temperature tick values that hold only along the bottom edge because the isotherms are skewed, profiles that run together in saturated layers, and kinks and inversions in the sounding.
