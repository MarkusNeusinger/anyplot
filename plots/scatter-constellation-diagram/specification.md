# scatter-constellation-diagram: Digital Modulation Constellation Diagram

## Description

An I/Q (In-phase/Quadrature) scatter plot showing symbol positions of a digitally modulated signal. Ideal constellation points are displayed as reference markers with received symbols scattered around them, revealing modulation quality and signal impairments such as noise, phase offset, and amplitude distortion. This plot is the standard diagnostic tool for evaluating digital modulation schemes like 16-QAM.

## Applications

- Wireless communications engineering: assessing modulation quality and signal integrity for QAM/PSK/APSK schemes
- Software-defined radio development: debugging demodulator performance and carrier recovery
- Standards compliance testing: verifying transmitter conformance for Wi-Fi, 5G NR, and DVB specifications
- Radar signal processing: analyzing digitally modulated waveform fidelity

## Data

- `i` (numeric) - In-phase component of each received symbol
- `q` (numeric) - Quadrature component of each received symbol
- `ideal_i` (numeric) - In-phase component of each ideal constellation point
- `ideal_q` (numeric) - Quadrature component of each ideal constellation point
- `symbol_index` (integer, optional) - Index mapping each received symbol to its nearest ideal point
- Size: 16 ideal points (4x4 grid for 16-QAM) with 500-2000 received symbols
- Example: A 16-QAM constellation with ideal points on a regular grid at +/-1, +/-3 and received symbols with additive Gaussian noise (SNR ~20 dB)

## Notes

- Use a 16-QAM modulation scheme as the primary example
- Show ideal constellation points as large, distinct markers (e.g., red crosses or circles)
- Show received symbols as smaller, semi-transparent dots clustered around ideal points
- Draw dashed decision boundary grid lines separating symbol regions
- Equal aspect ratio is required so the constellation geometry is accurate
- Label axes as "In-Phase (I)" and "Quadrature (Q)"
- Annotate EVM (Error Vector Magnitude) as a text label, e.g., "EVM = 5.2%"
- Center the plot at the origin with symmetric axis limits

## What a good version looks like

- A good version shows: the ideal constellation points as large, distinct markers, as the Notes ask, each at its ideal I and Q value and still recognizable through the received symbols around it in both themes.
- A good version shows: the received symbols as smaller, semi-transparent dots, as the Notes ask, each at its own I and Q value, never snapped to its ideal point or jittered, so that one cloud forms around each ideal point.
- A good version shows: dashed decision boundary lines separating the symbol regions, as the Notes ask, running midway between neighboring ideal points and staying subordinate to the symbols.
- A good version shows: an equal aspect ratio and a plot centered at the origin with symmetric axis limits, as the Notes ask, so the constellation's geometry is true, on axes labeled In-Phase (I) and Quadrature (Q).
- A good version shows: the EVM annotated as a text label, as the Notes ask, placed clear of the symbol clouds, with a value in keeping with the visible spread of the clouds.
- Expected, not a defect: received dots piling up into a dense cloud at every ideal point, stray symbols near or across a decision boundary, clouds of much the same size and shape everywhere under plain noise, and clouds stretched into arcs or pulled inward by phase or amplitude impairments.
