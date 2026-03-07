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
