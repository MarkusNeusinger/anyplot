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
