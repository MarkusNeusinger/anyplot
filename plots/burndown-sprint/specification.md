# burndown-sprint: Agile Sprint Burndown Chart

## Description

A sprint burndown chart tracks the amount of remaining work in an agile sprint over time, plotted as a step (or line) series that descends as tasks are completed. A straight ideal-burndown guideline runs diagonally from the total committed scope on day one down to zero on the final day, giving the team an at-a-glance reference for whether they are ahead of or behind schedule. It is one of the most widely used project-management visualizations in software development, surfacing scope creep, stalled progress, and end-of-sprint risk early enough to act on.

## Applications

- Daily Scrum tracking of remaining story points across a two-week sprint to forecast on-time completion
- Detecting scope changes mid-sprint, where the remaining-work line jumps up when new work is added
- Comparing actual progress against the ideal trajectory to flag a team that is consistently behind
- Release or milestone burndown over a longer horizon to communicate delivery confidence to stakeholders

## Data

- `day` (date) - calendar day of the sprint, from start date to end date
- `remaining` (numeric) - remaining work at the end of that day, in story points or task count
- `ideal` (numeric) - ideal remaining work for that day on the straight line from total scope to zero
- `scope_change` (numeric, optional) - signed change in total scope on that day, for scope-change markers (positive = work added)
- Size: 5-30 days (a typical sprint is 10 working days), single team
- Example: a 10-working-day sprint starting with 40 story points, burning down to 0, with a +8 point scope addition on day 4

## Notes

- Render the actual remaining work as a step series (work is completed in discrete chunks), or a straight line if the library makes steps awkward
- Draw the ideal burndown as a straight reference line from (start, total scope) to (end, 0), visually distinct (e.g. dashed, muted color)
- Y-axis starts at 0 and represents remaining work (story points or tasks); X-axis is the sprint timeline
- Shade weekends (non-working days) with a light background band to explain flat segments in the actual line
- Mark scope changes with a vertical line, arrow, or annotation where total scope shifts mid-sprint
- An optional burnup variant plots completed work rising toward a (possibly changing) total-scope line instead of remaining work falling to zero; keep the static, single-snapshot framing
- Include a legend distinguishing the actual series from the ideal guideline
- Below the ideal line is ahead of schedule; above it is behind — keep that reading obvious through color or annotation
