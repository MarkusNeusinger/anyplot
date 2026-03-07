# column-stratigraphic: Stratigraphic Column with Lithology Patterns

## Description

A vertical column visualization showing geological rock layers with standardized lithology patterns, formation names, ages, and thickness scales. Each layer is represented as a stacked rectangular block filled with a distinctive pattern (e.g., brick pattern for limestone, dots for sandstone, dashes for shale) following FGDC/USGS conventions. This plot is essential for communicating subsurface geology and sedimentary sequences in a compact, standardized format.

## Applications

- Stratigraphy: describing borehole or outcrop sections with standardized lithology symbols for geological reports
- Petroleum geology: visualizing well log lithological intervals alongside wireline log data
- Environmental geology: site characterization showing subsurface material types and aquifer geometry
- Geological education: teaching sedimentary sequences, unconformities, and stratigraphic principles

## Data

- `top` (numeric) - depth or elevation of the top of each layer in meters
- `bottom` (numeric) - depth or elevation of the bottom of each layer in meters
- `lithology` (categorical) - rock type for each layer (e.g., sandstone, limestone, shale, siltstone, conglomerate)
- `formation` (string) - formation or member name for each layer
- `age` (string) - geological age label (e.g., "Cretaceous", "65 Ma")
- Size: 5-20 layers
- Example: a synthetic sedimentary section with 8-10 layers of varying thickness and lithology, spanning multiple geological periods

## Notes

- Each lithology type should use a distinct fill pattern (hatching or texture) that approximates standard geological map symbols (e.g., brick pattern for limestone, stipple dots for sandstone, horizontal dashes for shale, random dashes for siltstone)
- The vertical axis represents depth or thickness (increasing downward by convention in borehole logs, or upward for outcrop sections); use increasing downward for this spec
- Formation names should be labeled to the right of or within each layer
- Age labels or geological period names should appear on the left side or as annotations
- A thickness/depth scale bar should be shown on the left axis with appropriate units (meters)
- Layer boundaries should be drawn as solid horizontal lines; unconformities may use wavy lines
- Use a minimum of 5 distinct lithology patterns to demonstrate variety
