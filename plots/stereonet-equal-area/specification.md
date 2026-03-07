# stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)

## Description

A Schmidt equal-area (lower-hemisphere) stereographic projection for plotting geological structural data. Great circles represent planar features (bedding, faults, joints) by their strike and dip, while poles to planes are plotted as points showing the orientation of the normal to each plane. Density contours highlight preferred orientations in clustered data. This is the standard projection used in structural geology for analyzing fabric elements and kinematic indicators.

## Applications

- Structural geology: mapping and analyzing fault, fracture, and bedding orientations from field measurements
- Geotechnical engineering: kinematic analysis for slope stability assessment using discontinuity orientations
- Mining geology: rock mass characterization by visualizing joint set distributions and their spatial relationships

## Data

- `strike` (numeric, degrees 0-360) - azimuth of the line of intersection between the plane and a horizontal surface
- `dip` (numeric, degrees 0-90) - angle of maximum inclination of the plane from horizontal
- `dip_direction` (numeric, degrees 0-360) - azimuth of the dip direction (alternative to strike, offset by 90 degrees)
- `feature_type` (categorical) - classification of the measurement (e.g., bedding, fault, joint, foliation)
- Size: 30-200 measurements typical for a single stereonet
- Example: field measurements of bedding planes and joint sets from a geological mapping campaign

## Notes

- Use lower-hemisphere equal-area (Schmidt net) projection; this preserves area relationships making density analysis meaningful
- Great circles should be drawn for planes; poles (points) plotted at 90 degrees to each plane
- The primitive circle represents the horizontal plane; North is at top (0/360 degrees)
- Include degree tick marks every 10 degrees around the perimeter and a North arrow or "N" label
- Color-code features by `feature_type` with a legend
- Overlay Kamb density contours on pole data to highlight preferred orientations
- Grid lines (equal-area net grid) should be subtle (light gray, thin lines) to avoid visual clutter
