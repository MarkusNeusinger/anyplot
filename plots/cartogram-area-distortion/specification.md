# cartogram-area-distortion: Cartogram with Area Distortion by Data Value

## Description

A cartogram distorts geographic regions so that their area becomes proportional to a data variable (e.g., population, GDP, election votes) rather than physical land area. This solves the classic problem of large but sparsely populated areas dominating standard maps, making it easier to compare values across regions at a glance. Contiguous cartograms preserve adjacency and rough shape of regions while rescaling them, famously used in election coverage worldwide.

## Applications

- Visualizing national election results where each state or district is sized by number of voters or electoral votes
- Comparing GDP or economic output across countries, avoiding the visual bias of geographically large but economically small regions
- Displaying population distribution across administrative regions to highlight urbanization patterns

## Data

- `region` (string) - Name or identifier of the geographic region (e.g., country, state, province)
- `geometry` (geometry) - Polygon or MultiPolygon boundary of each region (GeoJSON or shapefile format)
- `value` (numeric) - The data variable used to scale region area (e.g., population, GDP, votes)
- `label` (string, optional) - Display label or abbreviation for each region
- Size: 10-250 regions
- Example: US states sized by population, European countries sized by GDP

## Notes

- Prefer a contiguous cartogram (regions keep sharing borders after distortion) to preserve geographic context; where boundary geometry or a contiguous cartogram algorithm isn't available, a non-contiguous form (Dorling circles or Demers squares) is accepted, each region near its true position, shapes not overlapping, neighbors kept close
- Include original region outlines or a reference map inset for comparison
- Use a color scale to encode a secondary variable or to reinforce the size variable
- Label major regions with abbreviations for readability
- A legend should clarify what the area represents and the color encoding

## What a good version looks like

- A good version shows: each region's drawn area proportional to its value rather than to its land area, so a region with twice the value covers twice the area.
- A good version shows: preferably regions that still share borders with their real neighbors, in a rough shape that keeps the map recognizable, or else the Dorling circles or Demers squares the Notes accept, not overlapping; either way each region near its true position and close to its neighbors, as the Notes ask.
- A good version shows: the undistorted geography for comparison, as the Notes ask, either as the original region outlines or as a reference map inset.
- A good version shows: a color scale that encodes a secondary variable or reinforces the size variable, and a legend that says what the area represents and what the colors mean, as the Notes ask.
- A good version shows: abbreviations on the major regions, as the Notes ask, legible against their fill in both themes, while the smallest regions may stay unlabeled.
- Expected, not a defect: regions resized, stretched and moved away from their true outlines and coordinates, which is the point of the type; large regions with small values shrinking to slivers and compact ones swelling until the familiar map shape is gone.
