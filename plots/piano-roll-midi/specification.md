# piano-roll-midi: MIDI Piano Roll Visualization

## Description

A grid-based visualization of musical notes over time, as seen in digital audio workstations (DAWs). Each note is represented as a horizontal rectangle positioned by pitch (y-axis) and time (x-axis), with bar length indicating note duration and color indicating velocity (dynamics). The background alternates between white and dark rows to mirror piano keyboard layout, with vertical grid lines marking beats and measures.

## Applications

- Music production: visualizing and editing MIDI data in DAWs (Ableton Live, FL Studio, Logic Pro)
- Music analysis: examining melodic contour, rhythmic patterns, and harmonic structure of compositions
- Algorithmic composition: displaying output from generative music algorithms or AI-composed pieces
- Music education: teaching note relationships, intervals, and arrangement concepts visually

## Data

- `start` (float) - Note onset time in beats (e.g., 0.0, 1.5, 3.0)
- `duration` (float) - Note length in beats (e.g., 0.5 for eighth note, 1.0 for quarter note)
- `pitch` (int) - MIDI note number from 0-127 (e.g., 60 = Middle C / C4)
- `velocity` (int) - Note intensity from 0-127, mapped to color (low=soft/blue, high=loud/red)
- Size: 20-200 notes covering 4-16 measures
- Example: A short musical phrase or chord progression with varying dynamics

## Notes

- Y-axis should display note names (C4, D4, etc.) alongside or instead of raw MIDI numbers
- Background rows should alternate shading to distinguish black keys from white keys on a piano
- Vertical grid lines should mark beat divisions (quarter notes) with stronger lines at measure boundaries
- Color scale for velocity should use a sequential or diverging colormap (e.g., blue for piano/soft to red for forte/loud)
- The pitch range displayed should auto-fit to the data with a small margin, not show all 128 MIDI notes
