# spiral-timeseries: Spiral Time Series Chart

## Description

A time series plotted along a spiral (Archimedean or logarithmic), where each full revolution represents one cycle period (e.g., one year). By wrapping temporal data around a spiral, corresponding periods from different cycles align vertically, making recurring seasonal or periodic patterns immediately visible. This layout provides a compact alternative to long horizontal time series for cyclic data, revealing periodicity and trend simultaneously.

## Applications

- Visualizing yearly temperature or weather patterns across multiple years, with seasons aligned vertically
- Showing website traffic with weekly or monthly seasonality to identify recurring peaks
- Displaying retail sales cycles where holiday peaks align vertically across years
- Analyzing biological rhythms such as circadian or seasonal patterns in activity data

## Data

- `date` (datetime) — timestamp for each observation
- `value` (float) — measurement value at each timestamp
- `cycle_period` (str) — what defines one full revolution of the spiral (e.g., "year", "week", "month")
- Size: 2–10 full cycles, 100–3000 data points
- Example: Daily average temperatures over 5 years, with each year forming one spiral revolution

## Notes

- Each full revolution of the spiral corresponds to one cycle period
- Color or line thickness should encode value magnitude along the spiral
- Radial grid lines mark subdivisions within each cycle (e.g., months within a yearly spiral, days within a weekly spiral)
- Label the start of each cycle on the spiral for orientation
- The spiral should expand outward from center, with the earliest data closest to the center
- An Archimedean spiral (constant spacing between revolutions) is preferred for uniform readability
- Include a color bar or legend when using color mapping for values

## What a good version looks like

- A good version shows: the series along one continuous spiral in time order, the earliest data closest to the center and the spiral expanding outward, as the Notes ask, with no break or step where one cycle passes into the next.
- A good version shows: each full revolution covering exactly one cycle period, as the Notes ask, so the same phase of every cycle lies at the same angle and recurring patterns line up along a radius.
- A good version shows: the value encoded by color or line thickness along the spiral, as the Notes ask, with a color bar or legend when color is used; position on the spiral carries time only.
- A good version shows: radial grid lines marking the subdivisions within a cycle, labeled around the rim and lighter than the spiral, and the start of each cycle labeled on the spiral, as the Notes ask.
- A good version shows: revolutions that stay clear of each other, preferably with the constant spacing of the Archimedean spiral the Notes prefer.
- Expected, not a defect: inner revolutions that are shorter, so the same time span looks denser there, a first or last revolution that is incomplete, and abrupt color or thickness changes along the spiral where the data is noisy.
