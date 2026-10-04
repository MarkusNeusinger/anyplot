# slope-basic: Basic Slope Chart (Slopegraph)

## Description

A slope chart (slopegraph) visualizes changes between two time points by connecting values with lines across vertical axes. It emphasizes the direction and magnitude of change rather than absolute values, making it ideal for spotting increases, decreases, and rank changes at a glance. This chart type excels at before/after comparisons and highlighting which items improved or declined.

## Applications

- Comparing company performance metrics between two fiscal years
- Showing student test score changes from pre-test to post-test
- Visualizing country rankings before and after a policy change
- Tracking product satisfaction ratings between survey periods

## Data

- `entity` (categorical) - Items being compared (e.g., countries, products, students)
- `value_start` (numeric) - Value at first time point
- `value_end` (numeric) - Value at second time point
- Size: 5-15 entities for optimal readability
- Example: Sales figures for 10 products comparing Q1 vs Q4

## Notes

- Labels should appear at both endpoints for entity identification
- Consider color coding lines by direction (increase vs decrease)
- Vertical axes should be labeled with time point names
- Avoid too many entities (>15) as lines become difficult to follow

## What a good version looks like

- A good version shows: one straight line per entity joining its value at one time point to its value at the next, every end placed on one shared value scale so steepness reflects the size of the change, for few enough entities that each line can be followed, as the Notes ask.
- A good version shows: an entity label at both ends of every line, as the Notes ask, with the value beside it if drawn; where ends crowd, a label may shift along its axis to stay clear of its neighbors, but the line end stays at its value.
- A good version shows: each vertical axis labeled with the name of its time point, as the Notes ask.
- A good version shows: direction colors, if used as the Notes allow: one color for increases and another for decreases, applied to every line by its actual direction, told apart in both themes and explained in a legend or note.
- A good version shows: the basic variant's one line per entity with its end labels, besides the direction colors the Notes allow, and no reference or average lines, trend lines, lines or bands highlighted beyond the direction colors, or callouts.
- Expected, not a defect: lines that cross, lines of very different steepness including nearly flat ones, several lines ending close together, and a value scale that does not start at zero.
