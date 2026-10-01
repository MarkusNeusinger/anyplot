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

## What a good version looks like

- A good version shows: a round, undistorted net whose primitive circle is the horizontal plane, with North at the top marked by an arrow or an N label and degree tick marks every 10 degrees around the perimeter, as the Notes ask.
- A good version shows: planes as great-circle arcs in the lower-hemisphere equal-area projection the Notes ask for, each running from one end of its strike on the primitive to the other, bowed toward its dip direction and inside the primitive, steep planes nearly straight through the center and gentle ones near the rim.
- A good version shows: the pole to each plane as a point at 90 degrees to that plane, as the Notes ask, at its true projected position on the side opposite the dip direction, so poles of steep planes sit near the primitive and poles of gentle planes near the center.
- A good version shows: poles and great circles color-coded by feature type and explained in a legend, as the Notes ask, with the equal-area net grid, where drawn, in thin, light lines that stay behind the data.
- A good version shows: Kamb density contours overlaid on the pole data, as the Notes ask, closing around the pole clusters, kept inside the primitive and distinguishable from the great circles and from the feature-type colors.
- Expected, not a defect: many great circles crossing each other and the pole clusters, poles piled up within a cluster, poles lying across the net from their planes' arcs, a cluster of steep-plane poles and its contours split across opposite rims, and large empty parts of the net.
