# span-basic: Basic Span Plot (Highlighted Region)

## Description

A span plot highlights a specific region of interest on a chart using a shaded rectangular area that spans the full height or width of the plot. Vertical spans mark ranges along the x-axis (e.g., time periods), while horizontal spans mark ranges along the y-axis (e.g., value thresholds). The semi-transparent fill allows underlying data to remain visible while drawing attention to the highlighted region.

## Applications

- Marking recession periods or economic events on financial time series charts
- Highlighting acceptable/unacceptable value ranges or threshold zones on line plots
- Indicating maintenance windows, downtime periods, or significant events in operational dashboards

## Data

- `start` (numeric) - Start position of the span region
- `end` (numeric) - End position of the span region
- `direction` (categorical) - Either "vertical" (spans x-axis) or "horizontal" (spans y-axis)
- Size: 1-5 span regions overlaid on existing data
- Example: A line chart with dates on x-axis showing a shaded vertical span from 2008 to 2009 marking a recession period

## Notes

- Use semi-transparent fill (alpha 0.2-0.3) to keep underlying data visible
- Vertical spans are most common for time-based data (highlighting periods)
- Horizontal spans work well for threshold visualization (highlighting value ranges)
- Optional: include edge lines or text labels within the span region

## What a good version looks like

- A good version shows: each span as a shaded rectangle from its start to its end value on one axis, covering the whole plot area in the other direction: full height for a vertical span, full width for a horizontal one.
- A good version shows: a semi-transparent fill, as the Notes ask, through which the underlying data and gridlines stay visible in both themes, while the span stays distinct from the page.
- A good version shows: the underlying series drawn at its data values and unchanged inside the span, so the span highlights a range of it without hiding or altering it.
- A good version shows: edge lines and text labels, if drawn as the Notes allow, on the span's own boundaries and inside its region, with each label naming what the span marks and readable against the fill in both themes.
- A good version shows: the basic variant's few span regions over the underlying data, with the edge lines and in-span text labels the Notes allow, and no reference or mean lines, trend line, highlighted points, highlights besides the spans themselves, or callouts on data points.
- Expected, not a defect: spans of very different width, a span that reaches the edge of the plot area, and a darker or mixed patch where a vertical and a horizontal span overlap; blending is what overlapping translucent fills do.
