# heatmap-periodic-table: Periodic Table Property Heatmap

## Description

A periodic table of the elements rendered in its canonical layout — 18 groups across by 7 periods down, with the lanthanide and actinide series detached as two separate rows below — where each element tile is colored by a continuous property such as electronegativity, atomic radius, melting point, or first ionization energy. A colorbar maps tile color to property value, and every tile carries the element symbol and atomic number, optionally with the numeric property value. This visualization fuses an immediately recognizable fixed grid with heatmap encoding, turning a familiar reference chart into a tool for spotting periodic trends at a glance.

## Applications

- Teaching periodic trends in chemistry — electronegativity rising toward the top-right, atomic radius growing down a group — by letting students read the gradient directly off the table
- Comparing physical properties (melting point, density, first ionization energy) across the elements to highlight families and anomalies
- Materials-science screening, shading elements by abundance, cost, or a target property to identify candidate substitutions
- Science communication and reference posters where a single property is encoded onto the standard layout everyone already knows

## Data

- `symbol` (string) — element symbol (e.g., "H", "Fe", "Au")
- `atomic_number` (integer) — proton count, 1–118, shown on each tile
- `group` (integer) — column position, 1–18 (lanthanides/actinides handled by period/series placement)
- `period` (integer) — row position, 1–7
- `value` (numeric) — the continuous property mapped to tile color (e.g., electronegativity, atomic radius in pm, melting point in K)
- Size: up to 118 elements; typically the ~90–118 with a defined value for the chosen property
- Example: Pauling electronegativity for all elements, or first ionization energy in kJ/mol

## Notes

- Use the canonical layout: 18 groups × 7 periods, with the lanthanides (period 6) and actinides (period 7) pulled out into two rows offset below the main grid, leaving a gap at group 3 in those periods
- Tiles are equal-sized squares with a small gap; the f-block rows are visually separated from the main body
- Apply a sequential colormap for unipolar properties (e.g., viridis, plasma); a diverging map only if the property has a meaningful midpoint
- Render the element symbol prominently and the atomic number in a corner (typically top-left); optionally add the property value in smaller text below the symbol
- Ensure label text stays legible against the tile color — switch text between dark and light based on tile luminance
- Elements with no value for the chosen property should be drawn as empty/greyed tiles rather than omitted, preserving the recognizable shape
- Include a colorbar labeled with the property name and units
- Equal-area tiles and the fixed canonical shape are the defining characteristics — do not rescale tiles by value
