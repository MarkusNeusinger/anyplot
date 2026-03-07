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
