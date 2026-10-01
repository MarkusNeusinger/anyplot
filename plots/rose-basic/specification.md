# rose-basic: Basic Rose Chart

## Description

A rose chart (also called Nightingale or coxcomb diagram) displays categorical data in a circular format where segments are arranged around the center like pie slices, but with radius proportional to the value rather than angle. This visualization excels at showing cyclical or directional patterns where the circular arrangement has natural meaning. The equal-angle wedges make comparison of values across categories intuitive while emphasizing the periodic nature of the data.

## Applications

- Visualizing monthly sales, weather patterns, or other data with natural 12-month cycles
- Displaying wind direction frequency (wind rose) showing how often wind blows from each compass direction
- Comparing day-of-week patterns like customer visits, social media engagement, or energy consumption
- Showing hourly distributions where the circular clock face arrangement aids interpretation

## Data

- `category` (categorical) - Angular positions representing periodic categories (e.g., months, directions, hours)
- `value` (numeric) - Determines segment radius; larger values extend further from center
- Size: 4-24 categories typical; 8-12 optimal for readability
- Example: Monthly rainfall amounts, wind direction frequencies, or hourly traffic counts

## Notes

- Segment radius should be proportional to value (not area) for easier visual comparison
- Categories should have natural circular ordering (months, compass directions, hours)
- Use consistent color scheme; single color with varying saturation or distinct colors per category
- Start position typically at top (12 o'clock) for time data or north for directional data
- Include radial gridlines to aid value estimation

## What a good version looks like

- A good version shows: one wedge per category, all wedges of the same angle and together filling the circle, each reaching from the center to a radius proportional to its value (radius, not area, as the Notes ask) on a radial scale that starts at zero.
- A good version shows: the categories in their natural circular order (months, compass directions, hours), each labeled at its wedge, with the first one typically at the top, as the Notes describe.
- A good version shows: radial gridlines with value labels, as the Notes ask, lighter than the wedges and visible in both themes.
- A good version shows: one consistent color scheme, as the Notes ask: a single color, whose saturation may vary, or one distinct color per category, with neighboring wedges told apart by a thin separator or their colors.
- A good version shows: the basic variant's single value per category: besides the radial gridlines the Notes ask for, no stacked or subdivided wedges, second series, reference or mean lines or rings, highlighted wedges or sectors, or callouts and annotations of extrema.
- Expected, not a defect: wedges of very different radius, including one dominant wedge and one that is a sliver near the center, a lopsided outline, and large wedges that look more dominant than their values because wedge area grows faster than radius.
