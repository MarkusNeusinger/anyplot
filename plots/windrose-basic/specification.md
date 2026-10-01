# windrose-basic: Wind Rose Chart

## Description

A wind rose displays wind speed and direction data as a polar stacked histogram showing the frequency distribution of wind across compass directions. Each spoke represents a direction sector (typically 8-16 bins), with stacked colored segments indicating different wind speed ranges. This specialized meteorological visualization reveals dominant wind patterns, prevailing directions, and speed distributions simultaneously, making it essential for site assessment and environmental analysis.

## Applications

- Assessing wind farm site suitability by analyzing prevailing wind patterns and speed distributions
- Planning airport runway orientations based on historical wind direction frequencies
- Conducting air quality studies to understand pollutant dispersion patterns
- Designing building ventilation and urban planning based on local wind climatology

## Data

- `direction` (numeric) - Wind direction in degrees (0-360, where 0/360 is North)
- `speed` (numeric) - Wind speed in consistent units (m/s, km/h, or knots)
- `frequency` (numeric, optional) - Pre-aggregated frequency counts per direction/speed bin
- Size: 500-50000 observations recommended for meaningful distributions
- Example: Hourly wind measurements from a weather station over one year

## Notes

- Direction bins typically use 8 (N, NE, E, SE, S, SW, W, NW) or 16 sectors
- Speed bins should use meaningful ranges for the data (e.g., 0-5, 5-10, 10-15, 15+ m/s)
- North should be at the top (0 degrees) following meteorological convention
- Colors traditionally progress from cool (calm) to warm (strong) for speed bins
- Include a legend showing speed ranges and their colors
- Radial axis shows frequency (percentage or count) of observations per direction

## What a good version looks like

- A good version shows: one spoke per direction sector, all sectors of the same angular width, with north at the top, as the Notes ask, the other directions following clockwise in compass order, and compass labels around the rim.
- A good version shows: each spoke's total length as the frequency of observations from that direction, on a radial frequency axis that starts at zero at the center and has labeled rings in percent or counts, as the Notes say.
- A good version shows: every spoke stacked into speed-bin segments in the same speed order, each segment's radial length the frequency of its bin, with bin ranges that are meaningful for the data, as the Notes ask.
- A good version shows: one color per speed bin, the same in every spoke and traditionally running from cool for calm to warm for strong, as the Notes describe, with a legend that gives each bin's speed range, as the Notes ask.
- A good version shows: the basic variant's standard wind rose: besides the direction spokes, stacked speed bins, frequency rings and speed legend its spec asks for, no reference or mean lines or rings, highlighted sectors or spokes, callouts on the prevailing direction, or second rose.
- Expected, not a defect: a lopsided rose with long spokes at the prevailing directions and nearly empty sectors elsewhere, segments too thin to tell apart in rare directions and for the strongest speeds, and outer segments that cover more area than inner ones of the same frequency.
