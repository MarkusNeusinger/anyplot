# gantt-dependencies: Gantt Chart with Dependencies

## Description

A Gantt chart that visualizes project schedules with task dependencies and groupings. Beyond displaying task timelines, this chart shows relationships between tasks using connector arrows, indicating which tasks must complete before others can begin. Tasks can be organized into groups (phases or work packages) with aggregate timeline bars showing the span of each group. This visualization is essential for understanding critical paths and scheduling constraints in complex projects.

## Applications

- Project management to visualize task sequences and identify critical path dependencies
- Software development sprint planning showing feature dependencies and blockers
- Construction project scheduling where certain phases must complete before others begin
- Manufacturing workflow planning to coordinate sequential and parallel operations

## Data

- `task` (str) - Name or description of the task
- `start` (datetime) - Start date/time of the task
- `end` (datetime) - End date/time of the task
- `group` (str, optional) - Parent group or phase for hierarchical organization
- `depends_on` (list[str], optional) - List of task names that must complete before this task starts (finish-to-start unless `dependency_types` says otherwise)
- `dependency_types` (list[str], optional) - One per `depends_on` entry: FS, SS, FF or SF; default FS
- Size: 10-50 tasks for optimal readability with dependencies
- Example: Software project with phases like "Requirements", "Design", "Development", "Testing" where each phase contains multiple dependent tasks

## Notes

- For finish-to-start links, draw dependency arrows from the right edge (end date) of each predecessor bar to the left edge (start date) of the successor bar
- Use different visual styles for dependency types (finish-to-start is most common)
- Group headers should show aggregate timeline spanning from earliest to latest task in the group
- Consider indentation or color coding to distinguish groups from individual tasks
- Arrows should avoid overlapping task bars where possible
- Include a legend explaining dependency line styles if multiple types are used
- Finish-to-start successors must start at or after their predecessor's end — never before
- Vertical alignment should clearly show task hierarchy (groups above their child tasks)

## What a good version looks like

- A good version shows: one horizontal bar per task, each on its own named row, running from the task's start date to its end date on a shared time axis; bars sit at their dates and are never shifted to make room for arrows.
- A good version shows: each dependency as an arrow between the predecessor's and the successor's bars, a finish-to-start link running from the predecessor's right edge (end date) to the successor's left edge (start date) as the Notes ask, with no finish-to-start successor starting before its predecessor ends.
- A good version shows: arrows that run through the gaps between rows and around task bars where possible, as the Notes ask, each one traceable from its predecessor to its arrowhead in both themes.
- A good version shows: where the data has groups, a header row above each group's child tasks with an aggregate bar spanning from the group's earliest start to its latest end, as the Notes ask; indentation or color coding, if used, sets the group rows apart from the task rows.
- A good version shows: where more than one dependency type is drawn, a different line style for each type and a legend that explains the styles, as the Notes ask, with links of other types attached to the bar ends their type names.
- Expected, not a defect: arrows that cross each other, several arrows leaving or converging on one task, long arrows that span many rows, a gap between a predecessor's end and its successor's start, and tasks or group bars that overlap in time; they are the structure the chart exists to show.
