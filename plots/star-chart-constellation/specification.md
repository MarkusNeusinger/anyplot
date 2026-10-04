# star-chart-constellation: Star Chart with Constellations

## Description

A celestial map that plots stars on a sky projection (stereographic or azimuthal equidistant) with constellation stick-figure lines connecting notable stars. Star apparent magnitudes are represented by point size (brighter stars appear larger), and a coordinate grid overlays the chart for orientation. In the dark theme, a dark background mimics a night sky, making this an intuitive tool for identifying constellations and planning observations.

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
- Use a dark navy or black sky with white or pale-yellow stars in the dark theme; in the light theme, either keep a dark sky disc or use the printed-atlas style of dark stars on a light ground
- Draw a coordinate grid (RA/Dec) with labeled tick marks at regular intervals
- Optionally include the ecliptic line as a dashed curve and the Milky Way band as a faint filled region
- Limit displayed stars by a magnitude threshold (e.g., mag <= 5.0) to avoid clutter

## What a good version looks like

- A good version shows: every star at its right ascension and declination in a stereographic or azimuthal equidistant projection with a circular sky boundary, as the Notes ask, never moved to clear a label, the constellations shaped as they appear in the sky rather than mirrored.
- A good version shows: point size falling with magnitude, as the Notes ask, the brightest stars the largest dots and the faintest still visible; white or pale yellow stars on a dark navy or black sky in the dark theme, and in the light theme a dark sky disc or dark stars on a light ground, as the Notes allow.
- A good version shows: constellation stick figures as thin, semi-transparent lines that join exactly the star pairs in the data and end on their stars, fainter than the stars, with each constellation's name near the centroid of its stars, as the Notes ask.
- A good version shows: a right ascension and declination grid drawn in the same projection as the stars, with labeled tick marks at regular intervals, as the Notes ask, and fainter than the stars and constellation lines.
- A good version shows: the ecliptic, if drawn as the Notes allow, as a dashed curve, and the Milky Way, if drawn, as a faint filled band behind the stars, neither competing with the constellation figures.
- Expected, not a defect: many faint stars as tiny dots, no stars fainter than the magnitude limit the Notes allow, stars that belong to no stick figure, constellation shapes stretched toward the edge of the projection, and in the light theme a dark sky disc or the printed-atlas style.
