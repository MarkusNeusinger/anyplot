# subplot-mosaic: Mosaic Subplot Layout with Varying Sizes

## Description

A complex subplot layout where different subplots can have varying sizes and arrangements using intuitive ASCII-art style string definitions. Unlike GridSpec approaches that require explicit row/column spanning, mosaic layouts allow defining layouts through visual string patterns (e.g., "AB;CC" creates A and B on top, C spanning below), making complex configurations more readable and maintainable.

## Applications

- Dashboard layouts with a dominant visualization surrounded by smaller supporting charts
- Scientific figures where related plots need non-uniform visual emphasis
- Multi-panel reports combining wide time series with stacked detail panels
- Exploratory data analysis layouts with flexible panel arrangements

## Data

- `x` (numeric or categorical) - Primary variable for each subplot
- `y` (numeric) - Secondary variable for each subplot
- `z` (numeric, optional) - Tertiary variable for color or size encoding
- Size: Varies per subplot, typically 20-500 points per cell
- Example: Dashboard with wide overview chart (top), two medium detail charts (middle), and three small metric panels (bottom)

## Notes

- Layout defined using string patterns where repeated characters indicate spanning
- Support patterns like "AAB;AAB;CCC" for complex asymmetric layouts
- Allow empty cells using placeholder characters (e.g., "." for gaps)
- Maintain consistent spacing between all subplots
- Clear visual hierarchy with larger cells for primary data
- Each cell can contain a different plot type (line, bar, scatter, etc.)

## What a good version looks like

- A good version shows: panels of visibly different sizes, at least one spanning several rows or columns of the underlying grid; a panel's place and size come from the layout definition, not from data, while the marks inside each panel sit at their data values.
- A good version shows: the visual hierarchy the Notes ask for: the largest panel holds the primary data and the smaller panels hold supporting views.
- A good version shows: consistent spacing between all subplots, as the Notes ask, with the edges of a spanning panel flush with the outer edges of the panels it spans and no panel's tick labels, axis titles or legend running into a neighbor.
- A good version shows: every panel readable on its own: content suited to the panel's shape and size, and a title or axis labels that say what it shows.
- A good version shows: an empty cell, if the layout leaves one as the Notes allow, as a blank gap in the layout, not as an empty axes frame.
- Expected, not a defect: unequal panel sizes and aspect ratios, a layout that is not symmetric, different plot types, units and value ranges from panel to panel, small panels that show less detail than the large one, and a gap where the layout leaves a cell empty.
