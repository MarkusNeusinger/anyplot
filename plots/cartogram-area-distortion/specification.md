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

- Regions should remain contiguous (sharing borders) after distortion to preserve geographic context
- Include original region outlines or a reference map inset for comparison
- Use a color scale to encode a secondary variable or to reinforce the size variable
- Label major regions with abbreviations for readability
- A legend should clarify what the area represents and the color encoding
