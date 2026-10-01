# waveform-audio: Audio Waveform Plot

## Description

A time-domain visualization of audio amplitude that displays the raw waveform shape as seen in digital audio workstations (DAWs). The plot shows positive and negative amplitude symmetrically around a zero baseline, with time on the x-axis and normalized amplitude (-1 to +1) on the y-axis. This is the fundamental representation for inspecting audio signals, revealing dynamics, clipping, silence, and transient characteristics at a glance.

## Applications

- Audio engineering: inspecting recordings in DAWs to identify clipping, silence gaps, or dynamic range issues
- Speech analysis: visualizing spoken utterances for phonetic segmentation and timing analysis
- Seismology: displaying seismogram traces to identify earthquake P-wave and S-wave arrivals
- Biomedical signal processing: reviewing EEG or EMG waveforms for diagnostic patterns

## Data

- `time` (float) - time position in seconds from the start of the recording
- `amplitude` (float) - normalized signal amplitude ranging from -1.0 to +1.0
- Size: 5000-50000 samples (representing a short audio clip, e.g., 1-2 seconds at common sample rates)
- Example: a synthetically generated waveform combining a primary tone with harmonics, or a simulated speech-like signal with varying amplitude envelope

## Notes

- The waveform should be rendered as a filled area (mirrored above and below zero) or as a dense line plot, symmetric around the zero axis
- Use a semi-transparent fill color so overlapping regions remain visible
- Include a horizontal zero-line for reference
- X-axis should show time in seconds with appropriate precision
- Y-axis should display normalized amplitude from -1.0 to +1.0
- For dense waveforms, use min/max envelope rendering to avoid aliasing artifacts at lower zoom levels
- Generate synthetic audio data (e.g., a sine wave modulated by an amplitude envelope) rather than loading external audio files

## What a good version looks like

- A good version shows: time in seconds on the x axis and normalized amplitude on the y axis, the waveform drawn as a filled area mirrored above and below zero or as a dense line, as the Notes allow, symmetric around the zero axis.
- A good version shows: a y axis that displays the normalized amplitude range from -1.0 to +1.0, as the Notes ask, so the signal's level and headroom can be read against full scale.
- A good version shows: a horizontal zero line for reference, as the Notes ask, that can still be made out where the waveform is densest, in both themes.
- A good version shows: a fill, where the waveform is filled, in a semi-transparent color, as the Notes ask, so overlapping regions remain visible.
- A good version shows: for a dense waveform, an outline that follows the true peaks of every stretch, free of the moiré bands and dropped peaks that plain subsampling produces, which the min/max envelope the Notes ask for provides.
- Expected, not a defect: individual cycles merging into a solid band where thousands of samples share the width, quiet stretches collapsing onto the zero line, sudden transients, an outline that is not exactly mirror-symmetric, and peaks well inside the range or touching its limits.
