# titration-curve: Acid-Base Titration Curve

## Description

A titration curve plotting pH against volume of titrant added, producing the characteristic S-shaped (sigmoidal) curve used in analytical chemistry. The plot reveals buffer regions, equivalence points, and acid/base strength at a glance. Essential for chemistry education and laboratory analysis, it helps identify when a reaction reaches completion and which indicators are appropriate.

## Applications

- Determining the concentration of an unknown acid or base solution through volumetric analysis
- Identifying the equivalence point and selecting appropriate pH indicators for endpoint detection
- Teaching acid-base equilibrium, buffer capacity, and neutralization concepts in chemistry courses
- Quality control analysis in pharmaceutical manufacturing and food industry processes

## Data

- `volume_ml` (numeric) — volume of titrant added in mL, ranging from 0 to beyond the equivalence point
- `ph` (numeric) — measured pH value at each volume increment
- Size: 50-200 data points for a smooth curve
- Example: Strong acid/strong base titration (e.g., 25 mL of 0.1 M HCl titrated with 0.1 M NaOH)

## Notes

- Mark the equivalence point with a vertical dashed line and text annotation showing the volume and pH
- Include an optional derivative curve (dpH/dV) as a secondary y-axis overlay to precisely locate the equivalence point as the maximum of the derivative
- Shade the buffer region (typically the area around pH = pKa ± 1 for weak acid/base titrations) with a semi-transparent fill
- Use realistic titration data for a strong acid/strong base system (e.g., HCl + NaOH) where the equivalence point occurs at pH 7
- Label axes clearly: "Volume of NaOH added (mL)" on x-axis and "pH" on y-axis
- The y-axis should span pH 0-14 to show the full pH scale
