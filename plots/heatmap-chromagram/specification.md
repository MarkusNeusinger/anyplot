# heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)

## Description

A heatmap-style visualization showing the energy distribution across the 12 pitch classes (C, C#, D, D#, E, F, F#, G, G#, A, A#, B) over time. Each column represents a time frame and each row a pitch class, with color intensity indicating the energy or magnitude at that pitch-time point. Widely used in music information retrieval to analyze harmonic content, detect chords, estimate musical key, and study tonal progressions in audio signals.

## Applications

- Music information retrieval researchers analyzing chord progressions and detecting key changes in audio recordings
- Musicologists studying the harmonic structure and tonal patterns of classical or contemporary compositions
- Audio engineers comparing tonal fingerprints of different recordings for music similarity analysis
- Music educators visualizing harmonic progressions to teach students about chord theory and voice leading

## Data

- `time` (numeric) - time position of each frame in seconds
- `pitch_class` (categorical) - the 12 chromatic pitch classes: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
- `energy` (numeric) - energy or magnitude value at each time-pitch combination, typically from chroma feature extraction
- Size: 12 rows (pitch classes) x 50-500 time frames
- Example: chroma features extracted from a short musical passage showing chord changes over time

## Notes

- Y-axis must show all 12 pitch classes labeled clearly from C to B
- Use a sequential colormap (e.g., magma, inferno, or hot) to represent energy intensity
- Include a colorbar indicating the energy/magnitude scale
- Time axis should display seconds or beat positions
- Frame-by-frame resolution should be fine enough to capture chord transitions
- Synthetic data should simulate realistic harmonic patterns (e.g., alternating C major and G major chords)

## What a good version looks like

- A good version shows: all 12 pitch classes as rows on the y axis, each labeled, in chromatic order from C to B, as the Notes require, and time along the x axis in seconds or beat positions.
- A good version shows: every time frame as a column of cells at its time, the frames tiling the time axis, at a resolution fine enough that chord changes appear as sharp boundaries, as the Notes ask.
- A good version shows: a sequential colormap for energy and the color bar the Notes ask for, naming the energy or magnitude scale.
- A good version shows: harmonic content that reads as chords: a few pitch classes bright together over a stretch of time, forming horizontal bands that give way to another set at a chord change.
- Expected, not a defect: weaker energy in pitch classes outside the sounding chord from overtones and leakage, rows that are dark throughout, and bands broken at note onsets; a chromagram is striped by nature and is not to be smoothed.
