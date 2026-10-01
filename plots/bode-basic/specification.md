# bode-basic: Bode Plot for Frequency Response

## Description

A Bode plot displays a system's frequency response as two vertically aligned panels: magnitude (in decibels) on top and phase (in degrees) on the bottom, both plotted against frequency on a shared logarithmic scale. This visualization is fundamental in control systems engineering and signal processing for analyzing how a system responds to sinusoidal inputs across a range of frequencies, revealing stability characteristics, bandwidth, and resonance behavior.

## Applications

- Analyzing stability margins (gain margin and phase margin) of feedback control systems to ensure robust performance
- Designing and characterizing analog and digital filters in signal processing and audio engineering
- Evaluating amplifier frequency response and bandwidth limitations in electronics design
- Tuning PID controllers in industrial automation by examining open-loop transfer function behavior

## Data

- `frequency_hz` (numeric) - frequency values in Hz, logarithmically spaced (e.g., 0.01 to 10000 Hz)
- `magnitude_db` (numeric) - gain magnitude in decibels at each frequency point
- `phase_deg` (numeric) - phase shift in degrees at each frequency point
- Size: 100-1000 points (log-spaced for uniform coverage on logarithmic axis)
- Example: Second-order transfer function frequency response showing resonance peak and phase rolloff

## Notes

- Dual-panel layout with magnitude plot on top and phase plot on bottom, sharing a common logarithmic frequency axis
- Mark gain margin (dB above 0 dB at phase crossover frequency) and phase margin (degrees above -180 at gain crossover frequency) with annotations
- Draw reference lines at 0 dB on the magnitude plot and -180 on the phase plot
- Use logarithmic scale (log10) for the frequency axis in both panels
- Phase axis typically ranges from 0 to -180 (or -360 for higher-order systems)
- Consider using grid lines to aid reading of margin values

## What a good version looks like

- A good version shows: the magnitude panel on top and the phase panel below it, as the Notes ask, sharing one logarithmic frequency axis so every frequency lines up vertically across the two panels, with decade ticks that show the scale.
- A good version shows: in each panel the response as one continuous curve through its values in frequency order, magnitude in dB on the upper y axis and phase in degrees on the lower one.
- A good version shows: reference lines at 0 dB on the magnitude panel and at -180 on the phase panel, as the Notes ask, running across the whole frequency range, distinct from the response curves and visible in both themes.
- A good version shows: the gain margin marked at the phase crossover frequency, from the magnitude curve to the 0 dB line, and the phase margin at the gain crossover frequency, from the phase curve to the -180 line, each annotated, as the Notes ask, where the response has that crossover.
- A good version shows: the basic variant's standard Bode plot of one system: besides the 0 dB and -180 reference lines and the margin markings the Notes ask for and the grid lines the Notes suggest, no further reference lines, highlighted bands or callouts, no asymptote overlay and no second system.
- Expected, not a defect: a resonance peak that rises above the low-frequency gain, a steep phase drop around it, phase that runs on toward -360 for higher-order systems, margins that are small gaps beside the full axis range, and no gain margin marking for a response whose phase does not reach -180.
