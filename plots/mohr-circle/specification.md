# mohr-circle: Mohr's Circle for Stress Analysis

## Description

Mohr's Circle is a graphical method used to determine principal stresses, maximum shear stress, and stress transformations from a given 2D stress state. A circle is drawn on a normal stress (σ) vs. shear stress (τ) plane, with the center at ((σx + σy) / 2, 0) and a radius derived from the stress components. It is an essential tool in mechanical and civil engineering for visualizing how stress components change under coordinate rotation.

## Applications

- Determining principal stresses (σ1, σ2) in structural members under combined loading
- Finding maximum shear stress for failure analysis and material yielding criteria
- Visualizing stress transformation under arbitrary rotation angles in solid mechanics
- Teaching mechanics of materials concepts such as stress invariants and principal planes

## Data

- `sigma_x` (numeric) — normal stress in the x-direction (MPa)
- `sigma_y` (numeric) — normal stress in the y-direction (MPa)
- `tau_xy` (numeric) — shear stress on the xy-plane (MPa)
- Size: single stress state (3 values) defining the circle

## Notes

- Draw the circle with center at ((σx + σy) / 2, 0) and radius √(((σx − σy) / 2)² + τxy²)
- Mark the principal stresses (σ1, σ2) where the circle intersects the horizontal axis
- Show maximum shear stress (τ_max) at the top and bottom of the circle
- Plot the stress points A(σx, τxy) and B(σy, −τxy) on the circle
- Annotate the angle of the principal planes (2θp) as the angle from the reference points to the principal stress axis
- Use equal aspect ratio so the circle appears as a true circle
- Label axes: horizontal as "Normal Stress σ (MPa)", vertical as "Shear Stress τ (MPa)"
- Include a light grid and reference lines through the center for readability

## What a good version looks like

- A good version shows: a circle centered on the normal-stress axis at the mean of σx and σy with the radius the Notes give, on axes with an equal aspect ratio so it appears as a true circle, as the Notes ask.
- A good version shows: the principal stresses σ1 and σ2 marked where the circle meets the horizontal axis and the maximum shear stress at the top and bottom of the circle, as the Notes ask, each labeled at its true position.
- A good version shows: the stress points A at (σx, τxy) and B at (σy, −τxy) plotted on the circle, as the Notes ask, lying at opposite ends of a diameter through the center.
- A good version shows: the principal-plane angle 2θp annotated at the center, as the Notes ask, between the line to the reference point and the principal stress axis, with an arc, if drawn, spanning exactly that angle.
- A good version shows: the horizontal axis labeled as normal stress σ and the vertical as shear stress τ, both in MPa, with a light grid and reference lines through the center, as the Notes ask, all subordinate to the circle.
- Expected, not a defect: markers and labels gathering where a stress point, a principal stress and the angle arc lie close together, a circle that reaches into negative normal stress, empty margins left by the equal aspect ratio, and a shear axis that increases downward, as one common sign convention draws it.
