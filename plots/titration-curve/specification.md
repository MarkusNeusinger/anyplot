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
- For a weak acid or base titration, shade the buffer region (typically the area around pH = pKa ± 1) with a semi-transparent fill; a strong acid/strong base titration has none, so leave it unshaded or shade only a region labeled for what it is, never called a buffer
- Use realistic titration data for a strong acid/strong base system (e.g., HCl + NaOH) where the equivalence point occurs at pH 7
- Label axes clearly: "Volume of NaOH added (mL)" on x-axis and "pH" on y-axis
- The y-axis should span pH 0-14 to show the full pH scale

## What a good version looks like

- A good version shows: pH on the y axis against the volume of titrant added on the x axis, as one continuous S-shaped curve through the measured points, gently sloped before and after the equivalence point and near-vertical at it.
- A good version shows: the equivalence point marked with a vertical dashed line at its volume and a text annotation giving the volume and the pH, as the Notes ask, the line passing through the steepest part of the curve.
- A good version shows: the derivative curve dpH/dV, if drawn as the Notes allow, on a secondary y axis with its own label, peaking at the equivalence volume and visually subordinate to the pH curve.
- A good version shows: the buffer region, where the titration has one, shaded with a semi-transparent fill that leaves the curve visible, as the Notes ask; a strong acid/strong base titration has no buffer region, so a fill over a region labeled for what it is, never called a buffer, or no fill is equally valid.
- A good version shows: a y axis spanning the full pH scale from 0 to 14, as the Notes ask, and, for the strong acid/strong base system the Notes call for, the equivalence point at pH 7.
- Expected, not a defect: a jump so steep that it looks like a vertical line, a derivative that is one narrow spike on an otherwise flat trace, a curve that stops short of both ends of the pH axis, and no buffer shading for a strong acid/strong base titration.
