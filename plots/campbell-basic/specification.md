# campbell-basic: Campbell Diagram

## Description

A Campbell Diagram (also called an interference diagram) plots natural frequencies against rotational speed to identify critical speeds and resonance conditions in rotating machinery. It overlays engine order excitation lines (diagonal lines from the origin) on top of natural frequency curves, with intersections marking critical speeds where resonance may occur. This visualization is essential for ensuring safe operating ranges in turbomachinery, automotive powertrains, and other rotating equipment.

## Applications

- Rotordynamic analysis of turbomachinery (turbines, compressors, pumps) to identify critical speeds that must be avoided during operation
- Automotive powertrain NVH (Noise, Vibration, Harshness) engineering to map engine order excitations against structural modes
- Vibration analysis of rotating equipment during design validation to ensure natural frequencies are sufficiently separated from operating speed excitations

## Data

- `speed` (numeric) - Rotational speed in RPM, evenly spaced across the operating range (e.g., 0-6000 RPM)
- `frequency_mode_N` (numeric) - Natural frequency in Hz for each mode shape (4-5 modes), varying with rotational speed
- `engine_order` (numeric) - Integer multipliers (1x, 2x, 3x) defining diagonal excitation lines from the origin
- `critical_speeds` (numeric) - RPM values where engine order lines intersect natural frequency curves
- Size: 50-100 speed points per mode, 4-5 natural frequency curves, 3 engine order lines, 6-10 critical speed markers

## Notes

- Engine order lines are straight diagonal lines from the origin with slope = order_number / 60 (converting RPM to Hz)
- Natural frequency curves should show realistic behavior: slight variation with speed due to gyroscopic effects (some modes increase, some decrease with speed)
- Critical speed intersections should be marked with distinct markers (e.g., red circles or diamonds)
- Mode shapes should be labeled (e.g., "1st Bending", "2nd Bending", "1st Torsional", "Axial")
- Engine order lines should be labeled (e.g., "1x", "2x", "3x")
- Use a clean legend distinguishing natural frequency curves from engine order lines
- Optional: shade or highlight critical speed zones around intersection points

## What a good version looks like

- A good version shows: rotational speed on the x axis and frequency on the y axis, with each natural-frequency mode as one continuous curve across the speed range that varies only slightly with speed, some modes rising and some falling, as the Notes ask.
- A good version shows: the engine order lines as straight lines fanning out from the origin, each steeper in proportion to its order, as the Notes give, in a line style distinct from the mode curves and labeled with their order, as the Notes ask.
- A good version shows: the critical speeds marked with distinct markers, as the Notes ask, each sitting exactly where its engine order line crosses its mode curve and visible in both themes.
- A good version shows: every mode identified by its mode shape name and a legend that tells the natural-frequency curves from the engine order lines, as the Notes ask.
- A good version shows: the basic variant's standard Campbell diagram of one rotor: besides the engine order lines, critical speed markers and labels the Notes ask for and the shaded critical speed zones the Notes allow, no further reference lines, other highlighted bands, further callouts or damping panel.
- Expected, not a defect: critical speed markers bunching where several lines and curves cross within a narrow speed range, mode curves crossing one another, nearly flat mode curves, and steep engine order lines that leave through the top of the plot before the highest speed.
