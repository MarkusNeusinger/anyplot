# gantt-basic: Basic Gantt Chart

## Description

A Gantt chart is a horizontal bar chart that visualizes project schedules and timelines. Each task is represented as a horizontal bar spanning from its start date to end date, making it easy to see task durations, overlaps, and the overall project timeline at a glance. Gantt charts are essential for project management, helping teams understand task sequences and identify scheduling conflicts.

## Applications

- Project management and planning to track task progress and deadlines
- Resource allocation visualization showing when different resources are committed
- Manufacturing and production scheduling to coordinate sequential operations
- Event planning timelines to coordinate multiple parallel activities

## Data

- `task` (str) - Name or description of the task
- `start` (datetime) - Start date/time of the task
- `end` (datetime) - End date/time of the task
- `category` (str, optional) - Category or group for color coding tasks
- Size: 5-30 tasks for optimal readability
- Example: Project milestone data with phases like "Design", "Development", "Testing"

## Notes

- Horizontal bars should be clearly visible on a time axis (x-axis)
- Use clear date formatting on the x-axis (consider date range when choosing format)
- Consider color coding by category or status for better visual grouping
- Tasks should be ordered logically (by start date or category)
- Add a vertical line to indicate the current date when applicable
- Ensure adequate spacing between task bars for readability

## What a good version looks like

- A good version shows: one horizontal bar per task, each on its own row, running from the task's start date to its end date on a shared time axis, so bar length is the task's duration; bars sit at their dates and are never shifted or resized to tidy the layout.
- A good version shows: tasks in a logical order, as the Notes ask: by start date, so the bars step across the chart like a staircase, or by category, so related tasks sit together, with each task's name at its own row.
- A good version shows: bars of one thickness with a visible gap between neighboring rows, and color, if it encodes category or status as the Notes allow, as one distinct color per value named in a legend.
- A good version shows: date ticks on the time axis in a format that suits the chart's date range, as the Notes ask, so each bar's start and end can be read against them.
- A good version shows: the basic variant's task bars only, besides the current-date line the Notes ask for when applicable and the category or status colors they allow: no dependency arrows, group or summary bars, other reference lines, highlighted tasks or bands, or callouts.
- Expected, not a defect: tasks that overlap in time, idle gaps between tasks, bars of very different length, including a very short one, and a current-date line that cuts through the bars it crosses; an uneven schedule is the point of the chart, not an imbalance to fix.
