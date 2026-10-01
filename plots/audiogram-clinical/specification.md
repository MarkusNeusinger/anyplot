# audiogram-clinical: Clinical Audiogram

## Description

A standardized clinical audiogram that displays hearing test results, plotting hearing threshold (dB HL) against test frequency for each ear. The y-axis is inverted so that 0 dB HL (best hearing) sits at the top and increasing hearing loss extends downward, while the x-axis is logarithmic spanning the standard audiometric frequencies (125 Hz to 8 kHz). Thresholds are marked with the conventional symbols — a circle (O) for the right ear in red and a cross (X) for the left ear in blue — and connected per ear, with shaded horizontal bands indicating severity of hearing loss (normal, mild, moderate, severe, profound).

## Applications

- Audiology clinics recording and interpreting pure-tone audiometry results to diagnose and grade hearing loss
- ENT (otolaryngology) practices distinguishing conductive, sensorineural, and mixed hearing loss patterns across ears
- Occupational health programs screening for noise-induced hearing loss in workers exposed to loud environments
- Pediatric and educational audiology documenting hearing thresholds for hearing-aid fitting and follow-up

## Data

- `frequency` (int) - Test frequency in Hz on a logarithmic x-axis; standard values 125, 250, 500, 1000, 2000, 4000, 8000 (often also 750, 1500, 3000, 6000)
- `threshold_right` (int) - Right-ear hearing threshold in dB HL, plotted with red circle (O) markers
- `threshold_left` (int) - Left-ear hearing threshold in dB HL, plotted with blue cross (X) markers
- Size: 7-11 frequency points per ear
- Example: Pure-tone audiometry showing a typical high-frequency sensorineural notch (sloping loss toward 4-8 kHz)

## Notes

- Y-axis: hearing threshold in dB HL, **inverted** so 0 dB HL is at the top and values increase downward (typical range -10 to 120 dB HL, gridlines every 10 dB)
- X-axis: **logarithmic** frequency from 125 Hz to 8 kHz; label octave frequencies as ticks (125, 250, 500, 1k, 2k, 4k, 8k) using kHz shorthand where conventional
- Right ear: red, circle (O) marker, solid connecting line. Left ear: blue, cross (X) marker, solid connecting line (dashed line is an acceptable convention to distinguish ears)
- Connect thresholds within each ear in ascending frequency order; do not connect across ears
- Shade horizontal severity bands across the full width with labels: normal (-10–25 dB), mild (26–40), moderate (41–55) / moderately severe (56–70), severe (71–90), profound (>90). Use light, distinguishable fills that do not obscure the markers
- Include a legend mapping the O/red and X/blue symbols to right and left ear
- Keep the plot square-ish with a clear grid; the standardized appearance (inverted axis, log frequency, O/X symbols) is the defining feature and must be preserved
- Axis titles: x = "Frequency (Hz)", y = "Hearing Level (dB HL)"

## What a good version looks like

- A good version shows: hearing level in dB HL on an inverted y axis, 0 dB HL at the top and greater loss further down, against a logarithmic frequency axis from 125 Hz to 8 kHz with the octave frequencies as evenly spaced ticks, as the Notes ask.
- A good version shows: every threshold at its test frequency and dB level, the right ear as red circles (O) and the left ear as blue crosses (X), as the Notes ask, with a legend mapping the two symbols to the ears.
- A good version shows: one line per ear joining its thresholds in ascending frequency order, solid for both ears or dashed for the left as the Notes allow, and never a line running from one ear's symbols to the other's.
- A good version shows: the severity bands from normal to profound shaded across the full width at their dB ranges and labeled, as the Notes ask, in light fills that can be told apart in both themes and leave the markers and lines clearly visible.
- A good version shows: a square-ish plot area with a clear grid, as the Notes ask, so the slope of a hearing loss looks the same as on any other audiogram.
- Expected, not a defect: only a handful of points per ear at the discrete test frequencies, the O and X overlapping where both ears share a threshold, a steep slope or notch toward the high frequencies, lines crossing several severity bands, and empty lower bands when the loss is mild.
