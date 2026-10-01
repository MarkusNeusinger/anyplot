# line-annotated-events: Annotated Line Plot with Event Markers

## Description

A line plot with annotations at key points marking important events or milestones. This visualization enhances time series data by highlighting significant occurrences such as product launches, policy changes, or market events directly on the chart. Vertical lines, markers, and text labels draw attention to specific moments in time, making it easy to correlate data trends with real-world events.

## Applications

- Marking earnings announcements, dividends, or splits on a stock price chart
- Highlighting product releases or feature launches on user growth metrics
- Annotating policy changes or regulatory events on economic indicators
- Indicating equipment failures or maintenance windows on sensor data

## Data

- `date` (datetime) - Timestamp values for the continuous time series
- `value` (numeric) - Continuous measurements or observations at each timestamp
- `event_date` (datetime) - Timestamps of significant events to mark
- `event_label` (string) - Text description for each event marker
- Size: 50-500 points for the main series, 3-10 event markers
- Example: Daily stock prices over a year with quarterly earnings dates marked

## Notes

- Use vertical lines (axvline) to mark event dates clearly
- Position event labels to avoid overlapping with data or each other
- Consider rotating labels or using alternating heights for dense event clusters
- Event markers should be visually distinct from the data line (different color, dashed)
- Include a subtle legend or key if multiple event types are shown

## What a good version looks like

- A good version shows: one data line joining the values in time order, with every event marked by a vertical line at its own event date, as the Notes ask.
- A good version shows: event markers visually distinct from the data line, in a different color or a dashed style, visible in both themes without overpowering the line they annotate.
- A good version shows: a text label for every event, placed beside its marker so it is unambiguous which line it names, readable in both themes, and not covering the data line or another label.
- A good version shows: labels in a dense cluster of events kept apart, for example by the rotation or alternating heights the Notes suggest, rather than dropped or stacked on one another.
- A good version shows: a subtle legend or key for the event types, where more than one type is drawn.
- Expected, not a defect: unevenly spaced events, including several close together, labels at differing heights, and an event that coincides with no visible change in the series.
