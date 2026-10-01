# spectrum-basic: Frequency Spectrum Plot

## Description

A frequency spectrum plot displays signal amplitude or power across a range of frequencies, showing the frequency domain representation of time-series data. This visualization reveals the frequency components present in a signal, making it essential for identifying dominant frequencies, harmonics, and noise characteristics. It is fundamental in signal processing, audio engineering, and vibration analysis.

## Applications

- Analyzing audio signals to identify frequency content such as musical notes, speech formants, or noise interference
- Detecting machinery vibration patterns and identifying potential mechanical faults based on characteristic frequencies
- Examining electrical signals to find interference frequencies or verify filter performance

## Data

- `frequency` (numeric) - frequency values in Hz, typically from FFT computation
- `amplitude` (numeric) - signal amplitude or magnitude at each frequency, often in dB or linear scale
- Size: 256-4096 frequency bins (typical FFT sizes)
- Example: FFT output of a synthetic signal with multiple frequency components

## Notes

- Use logarithmic scale for frequency axis when spanning wide frequency ranges
- Power spectral density (dB scale) is common for comparing signals with different amplitudes
- Include clear axis labels with units (Hz for frequency, dB or linear for amplitude)
- Consider highlighting peak frequencies or annotating dominant components

## What a good version looks like

- A good version shows: frequency on the x axis and amplitude or power on the y axis, the spectrum drawn as a line, a filled line or thin stems with every bin at its own frequency and amplitude.
- A good version shows: a logarithmic frequency axis where the range is wide, as the Notes ask, with ticks that show it, and axis labels that give Hz for frequency and dB or the linear unit for amplitude, as the Notes ask.
- A good version shows: the dominant components as narrow peaks that stand out from the noise floor, on an amplitude range that shows the peaks and the floor together, where the signal has both.
- A good version shows: peak highlights or annotations, if drawn as the Notes suggest, each sitting at its peak and naming its frequency, kept to the dominant components.
- A good version shows: the basic variant's single spectrum: besides the peak highlights or annotations the Notes allow, no second signal or overlaid spectrum, reference or threshold lines, highlighted bands, further callouts, or waveform or spectrogram panel alongside.
- Expected, not a defect: a jagged noise floor across the bins, peaks that widen into skirts at their base from windowing, harmonics at regular multiples of a fundamental, bins that crowd together toward the high end of a logarithmic axis, and most of the plot area taken up by the floor.
