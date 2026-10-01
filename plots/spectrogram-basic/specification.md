# spectrogram-basic: Spectrogram Time-Frequency Heatmap

## Description

A spectrogram displaying time-frequency representation of a signal as a heatmap. It shows how the frequency content of a signal changes over time, with color intensity representing the amplitude or power at each time-frequency point. Essential for analyzing non-stationary signals where frequency characteristics vary, revealing patterns invisible in time-domain or frequency-domain views alone.

## Applications

- Audio analysis including speech recognition and music processing
- Vibration monitoring for machinery health and fault detection
- Seismic data analysis for earthquake and geological studies
- Biomedical signal processing such as EEG and ECG analysis

## Data

- `signal` (numeric array) - time-domain signal values
- `sample_rate` (numeric) - sampling frequency in Hz
- Size: 1000-50000 samples for clear visualization
- Example: chirp signal with increasing frequency, audio waveform, or vibration data

## Notes

- Use a perceptually uniform colormap (viridis, inferno) for accurate magnitude representation
- Include colorbar with power/amplitude units (dB scale often preferred)
- Label axes clearly: time (seconds) on x-axis, frequency (Hz) on y-axis
- Consider log scale for frequency axis when spanning multiple octaves
- Window size and overlap affect time-frequency resolution trade-off

## What a good version looks like

- A good version shows: time in seconds on the x axis and frequency in Hz on the y axis, both labeled as the Notes ask, with every time-frequency cell at its time and frequency; a logarithmic frequency axis, if used as the Notes suggest, has ticks that show it.
- A good version shows: a perceptually uniform colormap for the magnitude and a color bar that names the quantity and its unit, as the Notes ask, in decibels where that scale is used.
- A good version shows: a magnitude range on which weaker structure, where the signal has any, shows beside the strong components instead of vanishing into a uniformly dark field.
- A good version shows: a window that resolves the signal's features in both time and frequency, so a steady tone reads as a narrow horizontal ridge and a sweep as a continuous track, not as coarse blocks.
- A good version shows: the basic variant's single time-frequency image: besides the color bar the Notes ask for, no waveform or spectrum panel alongside, reference lines or frequency markers, highlighted regions or bands, callouts on components, or overlaid tracks.
- Expected, not a defect: sharp events smeared along time or pure tones smeared along frequency (the resolution trade-off the Notes name), a noise floor filling the background, large dark regions, and vertical streaks at abrupt onsets.
