# scatter-ashby-material: Ashby Material Selection Chart

## Description

A log-log scatter plot comparing two material properties (e.g., Young's modulus vs. density) with material families displayed as labeled bubble regions. Developed by Michael Ashby for systematic material selection in engineering design, this chart enables rapid visual comparison of material classes across multiple property dimensions. It is a standard tool in materials science and mechanical engineering education.

## Applications

- Selecting lightweight yet stiff materials for aerospace structural components by comparing Young's modulus against density
- Comparing thermal conductivity versus cost across material families for heat exchanger design
- Teaching materials science students to reason about trade-offs between competing material properties

## Data

- `material` (string) - Name of the individual material or data point
- `family` (string) - Material family/class (e.g., "Metals", "Polymers", "Ceramics", "Composites", "Foams", "Natural Materials")
- `property_x` (numeric) - First material property for the x-axis (e.g., density in kg/m^3)
- `property_y` (numeric) - Second material property for the y-axis (e.g., Young's modulus in GPa)
- Size: 50-200 data points across 5-8 material families
- Example: Classic density vs. Young's modulus Ashby chart with families including metals, polymers, ceramics, composites, elastomers, and foams

## Notes

- Both axes must use logarithmic scales to span the wide range of material properties
- Material families should be shown as colored bubble regions or convex-hull envelopes, not just individual points
- Each family region should have a clear text label
- Include axis labels with property name and units
- Use distinct colors for each material family
- Optionally include guide lines showing constant performance indices (e.g., E/rho for lightweight stiffness)

## What a good version looks like

- A good version shows: both axes on logarithmic scales, each labeled with its property name and units, as the Notes ask, and every material's point at its two property values.
- A good version shows: every material family as a colored bubble region or convex-hull envelope that encloses its points, as the Notes ask, in a color distinct from the other families, drawn so that its points and any overlapping neighbor region stay visible in both themes.
- A good version shows: a text label naming each family on or beside its region, as the Notes ask, readable against the region fill and the points and attributable to one region only.
- A good version shows: guide lines of constant performance index, if drawn as the Notes allow, as straight lines on the log-log axes, parallel for one index, labeled with the index they hold constant and lighter than the family regions.
- Expected, not a defect: family regions that overlap or touch where property ranges truly coincide, elongated or tilted envelopes, families of very different extent, points bunched inside their envelope, and large empty areas of the chart.
