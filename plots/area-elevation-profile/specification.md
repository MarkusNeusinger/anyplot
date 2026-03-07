# area-elevation-profile: Terrain Elevation Profile Along Transect

## Description

A cross-sectional line plot showing ground elevation along a path or transect line, with the area below the profile filled to create a terrain silhouette. Distance along the transect is plotted on the x-axis and elevation on the y-axis. This visualization is widely used in hiking and cycling route planning, civil engineering corridor design, and geomorphology to convey terrain shape and difficulty at a glance.

## Applications

- Hiking and trail planning: visualizing cumulative ascent, descent, and route difficulty along a trail
- Civil engineering: evaluating elevation changes along a proposed road or railway corridor
- Cycling stage profiles: showing climb categories and sprint points along a race stage (Tour de France style)
- GIS and geomorphology: extracting and analyzing terrain cross-sections from digital elevation models (DEMs)

## Data

- `distance` (numeric) - cumulative horizontal distance along the transect in km or miles
- `elevation` (numeric) - ground elevation at each sample point in meters or feet
- `landmark_name` (string, optional) - name of notable feature at that point (e.g., summit, pass, town)
- `landmark_distance` (numeric, optional) - distance value where the landmark is located
- `landmark_elevation` (numeric, optional) - elevation value where the landmark is located
- Size: 50-500 sample points along the transect
- Example: a 120 km hiking trail with elevation sampled every 250 m, featuring 6-8 labeled landmarks (summits, passes, huts)

## Notes

- The area below the profile line should be filled with a solid or gradient fill to create the terrain silhouette effect
- Label start and end points with location names and elevations
- Annotate key landmarks (summits, passes, river crossings) with vertical marker lines and text labels
- Use a vertical exaggeration factor (e.g., 10x) and note it on the plot to make terrain features visible
- Optional: apply gradient coloring to the profile line or fill based on slope steepness (green for flat, red for steep)
- The x-axis should show distance units, y-axis should show elevation units with appropriate tick spacing
