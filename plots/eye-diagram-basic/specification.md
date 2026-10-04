# eye-diagram-basic: Signal Integrity Eye Diagram

## Description

An eye diagram visualizes signal integrity by overlaying many periods of a digital signal onto a single time window spanning 1-2 unit intervals (UI). The overlapping traces form a characteristic eye-shaped opening whose height, width, and clarity reveal signal quality metrics such as jitter, noise, and inter-symbol interference (ISI). A wide-open eye indicates clean signal transmission, while a closed or blurred eye signals degradation.

## Applications

- Telecommunications engineering: characterizing high-speed serial links (PCIe, USB, HDMI) for compliance testing
- PCB design: validating signal integrity across traces, connectors, and backplanes
- Semiconductor testing: evaluating SerDes transmitter and receiver performance
- Fiber optics: assessing optical signal quality and link budget margins

## Data

- `time` (float) - Time within one unit interval, normalized to [0, 2] UI
- `voltage` (float) - Signal amplitude in volts at each time sample
- `trace_id` (int) - Identifier for each overlaid signal period (used to draw individual traces)
- Size: 200-500 overlaid traces, each with 100-200 samples per UI
- Example: Simulated NRZ (Non-Return-to-Zero) signal with random bit sequences, additive Gaussian noise, and random jitter applied to transition times

## Notes

- Use color intensity (density heatmap coloring) to show where traces overlap most frequently, with the dense end of the sequential colormap marking high trace density
- Time axis should be labeled in unit intervals (UI), not absolute time
- Voltage axis should show signal levels (e.g., 0 and 1 for NRZ)
- Generate synthetic data by simulating a random bit stream with controlled noise (sigma ~5% of amplitude) and jitter (sigma ~3% of UI)
- Smooth transitions between bit levels using a raised-cosine or sigmoid filter to simulate realistic bandwidth-limited signals
- Optionally annotate eye height and eye width measurements on the diagram

## What a good version looks like

- A good version shows: many signal periods overlaid in one time window, folded so that the transitions line up into crossings with an eye-shaped opening between them, on a time axis labeled in unit intervals (UI), as the Notes ask.
- A good version shows: density coloring, as the Notes ask: color intensity that rises with how often traces pass through a region, so the signal levels and the common transition paths stand out from rare excursions in both themes.
- A good version shows: a voltage axis that shows the signal levels, as the Notes ask, with the levels as the densest horizontal bands and an eye that stays open between them, in keeping with the modest noise and jitter the Notes specify.
- A good version shows: smooth, band-limited transitions between the levels, as the Notes ask, with rising and falling edges crossing each other, instead of square steps or straight ramps.
- A good version shows: the basic variant's single eye diagram: besides the density coloring the Notes ask for, a color bar for it and the eye height and eye width annotations the Notes allow, no compliance mask, reference or threshold lines, highlighted regions, other callouts, histogram panel or second signal.
- Expected, not a defect: overlapping traces too dense to follow one by one, levels and crossings thickened into fuzzy bands by noise and jitter, a few outlying traces reaching into the eye, and partial eyes cut off at the edges of the time window.
