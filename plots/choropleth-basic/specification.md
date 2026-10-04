# choropleth-basic: Choropleth Map with Regional Coloring

## Description

A choropleth map visualizes data by shading geographic regions (countries, states, or counties) according to a measured variable. This technique is ideal for showing regional patterns and spatial distributions, making it easy to identify areas with high or low values at a glance. The color intensity represents the data magnitude, creating an intuitive way to understand geographic variation.

## Applications

- Displaying population density or demographic statistics across countries or states
- Visualizing election results or voting patterns by region
- Showing economic indicators like GDP per capita or unemployment rates by geographic area
- Mapping disease prevalence or health outcomes across administrative regions

## Data

- `region_id` (string) - Geographic identifier (country ISO code, state FIPS code, or region name)
- `value` (numeric) - A rate, density or share per region (e.g., population density, unemployment rate, percentage); not a raw total
- Size: 10-200 regions (works best with moderate number of distinct areas)
- Example: Country-level population density, or a US state-level rate

## Notes

- Include a color legend showing the value range and corresponding colors
- Use an appropriate map projection (e.g., Robinson for world maps, Albers Equal Area for US)
- Consider using a sequential color palette for continuous data or diverging palette for data with a meaningful center point
- Ensure region boundaries are clearly visible but not overwhelming
- Handle missing data gracefully (show as gray or hatched pattern)

## What a good version looks like

- A good version shows: every region as a filled area with its real outline, in a map projection suited to the mapped extent, as the Notes ask, and shaded by its own value so the regional pattern reads from the fills alone.
- A good version shows: a color scale that fits the data (sequential, running from light to dark with the values, or diverging around a meaningful center) and a color legend, as the Notes ask, that shows the value range, either as a color bar or as class swatches with their bounds.
- A good version shows: region boundaries clearly visible but thinner and quieter than the fills, as the Notes ask, so neighbors of similar shade stay separate in both themes.
- A good version shows: regions whose value is missing, if any, in gray or a hatched pattern, as the Notes ask, distinct from every color of the scale so they never read as a low value.
- A good version shows: the basic variant's single shaded layer: besides the region boundaries, the color legend and the no-data style the Notes ask for and plain region name labels, no proportional symbols or point overlays, reference lines, highlighted regions, callouts or inset charts.
- Expected, not a defect: large regions dominating the picture while small ones are hard to make out, shapes and sizes distorted by the projection away from its center, and neighboring regions with very different shades.
