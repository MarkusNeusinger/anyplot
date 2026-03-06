# star-chart-constellation: Star Chart with Constellations

## Description

A celestial map that plots stars on a sky projection (stereographic or azimuthal equidistant) with constellation stick-figure lines connecting notable stars. Star apparent magnitudes are represented by point size (brighter stars appear larger), and a coordinate grid overlays the chart for orientation. The dark background mimics a night sky, making this an intuitive tool for identifying constellations and planning observations.

## Applications

- Amateur astronomy: planning observing sessions by visualizing which constellations are visible at a given time and location
- Education: teaching students celestial navigation, star identification, and the geometry of the celestial sphere
- Planetarium software: rendering an interactive or static sky view for public outreach and exhibits

## Data

- `star_id` (string) - unique identifier or common name for each star (e.g., "Sirius", "HIP 32349")
- `ra` (float) - Right Ascension in hours (0-24) or degrees (0-360)
- `dec` (float) - Declination in degrees (-90 to +90)
- `magnitude` (float) - apparent visual magnitude (lower values = brighter stars, typically -1.5 to 6.5)
- `constellation` (string) - IAU constellation abbreviation the star belongs to (e.g., "Ori", "UMa")
- `edges` (list of tuples) - pairs of star IDs that form constellation stick-figure lines
- Size: 200-500 stars covering 20-30 constellations for a clear, readable chart

## Notes

- Use a stereographic or azimuthal equidistant projection so the circular sky boundary looks natural
- Invert magnitude for point sizing: brighter stars (lower magnitude) should map to larger points
- Draw constellation lines as thin, semi-transparent lines connecting star pairs
- Label constellation names near the centroid of each constellation's star group
- Use a dark navy or black background with white or pale-yellow stars
- Draw a coordinate grid (RA/Dec) with labeled tick marks at regular intervals
- Optionally include the ecliptic line as a dashed curve and the Milky Way band as a faint filled region
- Limit displayed stars by a magnitude threshold (e.g., mag <= 5.0) to avoid clutter
