# map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison

## Description

A tile grid map represents geographic regions (states, countries, provinces) as equally-sized tiles — squares or hexagons — arranged to approximate their real-world geographic positions. Unlike choropleth maps where large-area regions dominate visually, every region receives identical visual weight, making tile grid maps ideal for per-capita or per-region comparisons where the statistic matters more than physical area. Tiles are colored by a data variable and labeled with region abbreviations for identification.

## Applications

- Comparing US state-level election results without geographic area bias distorting the visual impression
- Showing per-country statistics across Europe with each nation given equal visual weight regardless of land area
- Displaying regional health metrics (vaccination rates, disease incidence) without geographic size distortion
- Visualizing technology adoption rates or policy compliance across administrative regions

## Data

- `region` (string) — Region identifier or abbreviation (e.g., "CA", "TX", "DE")
- `value` (numeric) — Metric to display via tile color (e.g., rate, percentage, count)
- `row` (integer) — Grid row position for the tile (0-indexed from top)
- `col` (integer) — Grid column position for the tile (0-indexed from left)
- Size: 10–60 regions
- Example: US states with per-capita income, EU countries with renewable energy percentage

## Notes

- Tiles may be squares or hexagons — both are valid approaches
- Color tiles using a sequential colormap for unipolar data or a diverging colormap when a meaningful midpoint exists
- Label each tile with the region abbreviation, ensuring text is legible against the tile color
- Include a colorbar or legend showing the value-to-color mapping
- Predefined grid layouts are commonly available for US states and European countries
- Maintain consistent tile sizing — equal area for all tiles is the defining characteristic
