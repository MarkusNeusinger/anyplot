# timeline-basic: Event Timeline

## Description

A timeline visualization that displays events and milestones along a temporal axis. Events are represented as points or markers with accompanying labels, making it easy to understand the sequence and timing of events. This plot type excels at showing chronological progressions and is particularly effective for communicating project phases, historical events, or any time-ordered sequence of occurrences.

## Applications

- Tracking project milestones and deliverables in software development or construction projects
- Visualizing historical events for educational presentations or museum displays
- Presenting product roadmaps to stakeholders showing feature releases over time
- Displaying company history or biographical timelines for annual reports

## Data

- `date` (datetime) - The date or timestamp when the event occurred
- `event` (string) - The name or short description of the event
- `category` (string, optional) - A grouping category for color-coding related events
- Size: 5-50 events for readability
- Example: Project milestone data with dates, milestone names, and phase categories

## Notes

- Horizontal orientation is most common for reading left-to-right
- Alternate label positions above and below the axis to prevent text overlap
- Use clear date formatting appropriate to the time scale (days, months, years)
- Consider color-coding by category when multiple event types exist
- For dense timelines, ensure adequate spacing or implement zooming capabilities

## What a good version looks like

- A good version shows: one marker per event at its date on a single time axis, horizontal in the most common layout, so the distance between markers is the time between events; markers are never moved or evenly spaced to make room for labels.
- A good version shows: each event's label tied to its marker by a connector or by sitting next to it, with labels alternating between the two sides of the axis (above and below on a horizontal timeline), as the Notes ask, so neighboring labels do not collide.
- A good version shows: date ticks or date labels in a format that suits the time scale (days, months or years), as the Notes ask.
- A good version shows: marker color, if it encodes category as the Notes allow, as one distinct color per category named in a legend.
- A good version shows: the basic variant's event markers, labels and connectors, besides the category colors the Notes allow: no duration bars or spans, second track of events, trend or reference lines, highlighted events or period bands, or callouts beyond the event labels.
- Expected, not a defect: uneven spacing, with clusters of close events and long empty stretches, labels at different distances from the axis on connectors of different length, and no value axis; a label's offset is layout that carries no value, only the marker's date is data.
