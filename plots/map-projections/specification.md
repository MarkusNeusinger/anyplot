# map-projections: World Map with Different Projections

## Description

A world map demonstrating different cartographic projections and their distortion characteristics. This visualization showcases how the same geographic data appears under various map projections (Mercator, Robinson, Mollweide, Orthographic, etc.), revealing how each projection preserves or distorts area, shape, distance, or direction. The plot includes graticule (latitude/longitude grid lines) and optionally Tissot indicatrices to illustrate projection distortion patterns.

## Applications

- Educational cartography demonstrating how map projections transform the spherical Earth to a flat surface
- Comparing projection suitability for different geographic analyses or presentations
- Visualizing global data with area-accurate projections to avoid misleading size comparisons
- Teaching geographic information systems (GIS) concepts about coordinate reference systems

## Data

- World country boundaries (GeoJSON format or shapefile)
- `country` (string) - Country identifier or ISO code
- `value` (numeric, optional) - Data variable for choropleth coloring
- Size: ~200 countries (world boundaries dataset)
- Example: Natural Earth world boundaries, country-level statistics

## Notes

- Support multiple projections: Mercator, Robinson, Mollweide, Orthographic, Equal Earth, Lambert Cylindrical, or other common projections
- Display graticule (latitude/longitude grid lines) at regular intervals (e.g., every 30 degrees)
- Show clean coastlines and country borders with appropriate styling
- Optional: Include Tissot indicatrices (circles that show distortion) to visualize how the projection affects area and shape
- Use a neutral color scheme for land masses when not showing data values
- Consider showing the same map in multiple projections side-by-side for comparison, or a single projection with clear title indicating which one

## What a good version looks like

- A good version shows: the world's coastlines and country borders drawn through each projection, as the Notes ask, with land clearly set apart from sea and in a neutral color unless it is colored by data values.
- A good version shows: a graticule of latitude and longitude lines at regular intervals, as the Notes ask, transformed by the same projection so its curvature shows how the projection bends the globe, and lighter than the coastlines.
- A good version shows: every map named by its projection: several projections side by side, each with its own label and the same world and styling so only the projection differs, or a single projection whose title says which one, as the Notes allow both.
- A good version shows: Tissot indicatrices, if drawn as the Notes allow, at regularly spaced positions, staying circular but changing size on a conformal projection and keeping their area but changing shape on an equal-area one.
- A good version shows: choropleth coloring by the optional value, if used, with a color legend, applied identically in every projection shown.
- Expected, not a defect: landmasses that differ in size and shape from one projection to the next, polar regions hugely inflated in Mercator, an orthographic view showing one hemisphere only, and map outlines of different shapes; distortion is the subject.
