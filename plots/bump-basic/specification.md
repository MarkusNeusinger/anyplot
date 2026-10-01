# bump-basic: Basic Bump Chart

## Description

A bump chart visualizes how rankings change over time by plotting rank positions and connecting them with lines. Unlike line charts that show values, bump charts focus specifically on ordinal rankings, making it easy to track position changes, overtakes, and rank stability across time periods.

## Applications

- Sports league standings tracking over a season
- Company market share ranking changes over quarters
- Product popularity rankings across time periods
- Election polling position changes over campaign weeks

## Data

- `entity` (categorical) - The items being ranked (teams, companies, products)
- `period` (categorical or time) - Time points for ranking snapshots
- `rank` (integer) - Position at each period (1 = highest rank)
- Size: 5-10 entities, 4-8 periods typical
- Example: Formula 1 driver standings over a 10-race season

## Notes

- Y-axis should be inverted (rank 1 at top)
- Use distinct colors or labels for each entity
- Consider dot markers at each period for clarity
- Lines should connect same entity across all periods

## What a good version looks like

- A good version shows: one line per entity passing through its rank at every period, in period order and with no period skipped, as the Notes ask, straight or gently curved between periods but never off its rank at a period.
- A good version shows: a rank axis inverted so that rank 1 is at the top, as the Notes ask, with ticks only at whole-number ranks.
- A good version shows: every entity identifiable along its whole line by a distinct color, a direct label at its line, or both, as the Notes ask, with colors told apart in both themes and labels not colliding with each other.
- A good version shows: dot markers, if drawn as the Notes allow, centered on the rank at each period, in their line's color.
- A good version shows: the basic variant's one line per entity with the markers and entity labels the Notes allow, and no reference lines, highlighted or faded lines, shaded rank bands, value-sized markers or lines, or callouts such as overtake notes.
- Expected, not a defect: lines that cross, several crossings between the same two periods, lines that run flat while a rank holds, and steep jumps over many ranks; the crossings are the overtakes the chart exists to show.
