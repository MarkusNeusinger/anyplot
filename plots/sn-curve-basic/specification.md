# sn-curve-basic: S-N Curve (Wöhler Curve)

## Description

An S-N curve (also known as a Wöhler curve) visualizes the relationship between alternating stress amplitude and the number of cycles to failure for a material under fatigue loading. Both axes typically use logarithmic scales, with stress on the y-axis and cycle count on the x-axis. This plot is fundamental for predicting material fatigue life and identifying key material properties such as ultimate strength, yield strength, and endurance limit.

## Applications

- Analyzing fatigue test data from metal coupon testing machines to characterize material behavior
- Predicting the fatigue life of mechanical components subjected to cyclic loading using Miner's Rule
- Comparing fatigue resistance between different materials or alloys for engineering design decisions
- Identifying the endurance limit to determine safe operating stress levels for infinite life design

## Data

- `cycles` (numeric) - Number of cycles to failure (N), typically ranging from 1 to 10^7 or more
- `stress` (numeric) - Alternating stress amplitude or range in MPa or ksi
- Size: 10-100 data points from fatigue tests, often with multiple samples at each stress level
- Example: Fatigue test results showing stress levels vs. cycles to failure for steel specimens

## Notes

- Both axes should use logarithmic scales for proper visualization of the wide range of values
- Include horizontal reference lines for key material properties: Ultimate Strength, Yield Strength, and Endurance Limit
- The curve typically shows three distinct regions: low-cycle fatigue (plastic), high-cycle fatigue (elastic), and infinite life (below endurance limit)
- Data points may include scatter from multiple test specimens at the same stress level
- A power-law or Basquin equation fit line is commonly overlaid on the data points

## What a good version looks like

- A good version shows: stress on the y axis against cycles to failure on the x axis, both on logarithmic scales, as the Notes ask, with ticks that show the scales and every test result as a point at its own cycle count and stress.
- A good version shows: horizontal reference lines for ultimate strength, yield strength and endurance limit, as the Notes ask, each at its stress value, labeled by name and visible in both themes.
- A good version shows: a power-law or Basquin fit line, if overlaid as the Notes suggest, running through the middle of the scatter along the sloping part of the data, distinct from the points and from the reference lines.
- A good version shows: points that fall from high stress at few cycles toward the endurance limit at many cycles, so that the low-cycle, high-cycle and infinite-life regions the Notes describe can be read where the data spans them.
- A good version shows: the basic variant's single material: besides the three reference lines the Notes ask for, the fit line the Notes suggest and plain labels or light shading for the three regions the Notes name, no second material, further reference lines, highlighted points, callouts, or probability bands.
- Expected, not a defect: several specimens at one stress level spread widely along the cycle axis and partly overlapping, a fit line that misses individual points, unbroken run-out specimens marked with arrows at the longest lives, and a stress axis that spans far fewer decades than the cycle axis.
