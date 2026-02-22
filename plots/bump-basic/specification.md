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
