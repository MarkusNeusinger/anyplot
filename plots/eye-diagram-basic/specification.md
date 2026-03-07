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

- Use color intensity (density heatmap coloring) to show where traces overlap most frequently, with hot colors indicating high trace density
- Time axis should be labeled in unit intervals (UI), not absolute time
- Voltage axis should show signal levels (e.g., 0 and 1 for NRZ)
- Generate synthetic data by simulating a random bit stream with controlled noise (sigma ~5% of amplitude) and jitter (sigma ~3% of UI)
- Smooth transitions between bit levels using a raised-cosine or sigmoid filter to simulate realistic bandwidth-limited signals
- Optionally annotate eye height and eye width measurements on the diagram
