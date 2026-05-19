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
