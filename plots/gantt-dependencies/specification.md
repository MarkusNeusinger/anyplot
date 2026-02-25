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
- `depends_on` (list[str], optional) - List of task names that must complete before this task starts
- Size: 10-50 tasks for optimal readability with dependencies
- Example: Software project with phases like "Requirements", "Design", "Development", "Testing" where each phase contains multiple dependent tasks

## Notes

- Draw dependency arrows from the right edge (end date) of each predecessor bar to the left edge (start date) of the successor bar
- Use different visual styles for dependency types (finish-to-start is most common)
- Group headers should show aggregate timeline spanning from earliest to latest task in the group
- Consider indentation or color coding to distinguish groups from individual tasks
- Arrows should avoid overlapping task bars where possible
- Include a legend explaining dependency line styles if multiple types are used
- Dependent tasks must be scheduled to start at or after the end of their predecessor — never before
- Vertical alignment should clearly show task hierarchy (groups above their child tasks)
