# scatter-hr-diagram: Hertzsprung-Russell Diagram

## Description

The Hertzsprung-Russell (HR) diagram is the iconic astrophysics scatter plot that shows stellar luminosity (or absolute magnitude) versus surface temperature (or spectral class). Stars naturally cluster along the main sequence diagonal, with distinct regions for red giants, supergiants, and white dwarfs, revealing the fundamental relationship between stellar temperature and brightness.

## Applications

- Astrophysics research: classifying stellar populations and studying stellar evolution pathways
- Astronomy education: teaching students about stellar life cycles and spectral classification
- Observational astronomy: determining cluster ages by fitting main sequence turnoff points

## Data

- `temperature` (numeric) - Surface temperature in Kelvin (range ~2,000-40,000 K)
- `luminosity` (numeric) - Luminosity relative to the Sun (log scale, range ~0.0001-1,000,000)
- `spectral_type` (categorical) - Spectral classification (O, B, A, F, G, K, M)
- `star_name` (string) - Star identifier for notable labeled stars
- `region` (categorical) - Classification region (main sequence, red giants, supergiants, white dwarfs)
- Size: 100-500 stars representing different stellar populations
- Example: Synthetic dataset spanning all spectral types with the Sun as a marked reference point

## Notes

- X-axis must be reversed (high temperature/blue on left, low temperature/red on right) following the astrophysical convention
- Y-axis should use logarithmic scale for luminosity
- Points should be color-coded by spectral type using conventional colors (blue for O/B, white for A, yellow for F/G, orange for K, red for M)
- Label the four main regions: main sequence, red giants, supergiants, white dwarfs
- Mark the Sun's position as a distinct reference point
- Optional: include secondary x-axis labels showing spectral class (O, B, A, F, G, K, M)
