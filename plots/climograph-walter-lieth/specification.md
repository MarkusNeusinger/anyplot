# climograph-walter-lieth: Walter-Lieth Climate Diagram

## Description

A Walter-Lieth climate diagram (climograph) is the canonical visualization of a location's annual climate, plotting monthly mean temperature and monthly precipitation over the twelve months on a single panel. It uses the classic 1:2 axis-scaling convention where 10 °C on the temperature axis aligns with 20 mm on the precipitation axis, so the relationship between the two curves directly reveals water availability: where precipitation exceeds the temperature curve the period is humid (filled blue/hatched), and where the temperature curve rises above precipitation the period is arid (filled red/dotted). A header carries station metadata and annual means, while frost indicators along the baseline mark cold months.

## Applications

- Teaching biogeography, ecology, and climatology students to read seasonal humid and arid periods at a glance
- Comparing the climate signature of different stations or biomes (Mediterranean, tropical, continental) using a standardized layout
- Characterizing a site's growing season and drought stress for agronomy, forestry, or vegetation studies
- Summarizing long-term climate normals (e.g., 1991–2020) for a weather station in a single reference figure

## Data

- `month` (categorical/ordinal) - The twelve months in order (Jan–Dec), typically shown as single-letter or three-letter labels on the x-axis
- `temperature` (numeric) - Monthly mean temperature in degrees Celsius (left y-axis)
- `precipitation` (numeric) - Monthly total precipitation in millimeters (right y-axis, scaled 2:1 against temperature)
- `station_name` (text, metadata) - Station or location name shown in the header
- `elevation` (numeric, metadata) - Station elevation in meters, shown in the header
- `temp_annual_mean` (numeric, metadata) - Annual mean temperature for the header
- `precip_annual_total` (numeric, metadata) - Annual total precipitation for the header
- Size: exactly 12 rows (one per month)
- Example: A climate normal table for a single station, e.g. a Mediterranean station showing a summer arid period

## Notes

- Apply the fixed Walter-Lieth scaling convention: the precipitation axis is 2× the temperature axis (10 °C ↔ 20 mm) so the two curves are directly comparable; above 100 mm precipitation the scale is conventionally compressed (10:1) and that upper band is filled solid blue to indicate a perhumid (very wet) period
- Temperature is drawn as a line on the left axis (often red); precipitation as a line (or bars) on the right axis (often blue)
- Fill the area between the curves: blue/hatched where precipitation > temperature curve (humid period), red/dotted where temperature > precipitation (arid period) — this is the diagram's defining visual feature
- Header should display station name, elevation, and the annual mean temperature and annual precipitation total in the conventional position
- Indicate frost months along the baseline: typically a colored band/blocks beneath the x-axis marking months with mean temperature below 0 °C (likely frost) and a lighter band for months with absolute minimum below 0 °C if available
- Left axis ticks conventionally at 0, 10, 20, 30 °C; right axis ticks at 0, 20, 40, 60, 100 mm to preserve the alignment
- The plot is fully static-renderable with no interactivity required
