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

## What a good version looks like

- A good version shows: each note as a horizontal rectangle in the row of its pitch, starting at its onset beat and as long as its duration, with higher pitches higher up; notes sit at their data values and are never snapped or stretched to the grid.
- A good version shows: a pitch axis labeled with note names, alongside or instead of MIDI numbers, and fitted to the pitches in the data with a small margin rather than showing all 128 MIDI notes, as the Notes ask.
- A good version shows: background rows shaded in the piano keyboard's pattern, as the Notes ask, with black-key rows distinguishable from white-key rows in both themes and the shading staying behind the notes.
- A good version shows: vertical grid lines at the beats with visibly stronger lines at the measure boundaries, as the Notes ask, all drawn behind the notes.
- A good version shows: note color from velocity on one sequential or diverging scale, as the Notes ask, with a color bar or legend that says which end is soft and which is loud, and every note distinguishable from both row shades in both themes.
- Expected, not a defect: notes stacked at the same beat in chords, notes of very different length, including very short ones, rests and empty pitch rows inside the range, and repeated notes that touch end to start in one row; they are the music, not gaps or clutter to fix.
