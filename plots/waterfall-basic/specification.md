# waterfall-basic: Basic Waterfall Chart

## Description

A waterfall chart visualizes how an initial value is affected by a series of intermediate positive or negative values, leading to a final value. Each bar represents a change from the previous cumulative total, with positive values extending upward and negative values extending downward. This chart type is essential for understanding cumulative effects and breaking down the components that contribute to a final result.

## Applications

- Financial analysis: breaking down revenue to net profit through costs, taxes, and adjustments
- Inventory management: tracking stock levels through additions and withdrawals over time
- Project cost tracking: visualizing budget changes through additions and reductions
- Sales pipeline progression: showing conversion rates and drop-offs through stages

## Data

- `category` (string) - step labels describing each change (e.g., "Starting Balance", "Sales", "Costs", "Taxes", "Net Profit")
- `value` (numeric) - change values (positive for increases, negative for decreases)
- Size: 5-15 steps
- Example: quarterly financial breakdown from revenue to net income

## Notes

- Color positive and negative changes differently (e.g., green for positive, red for negative)
- Show connecting lines between bars to emphasize the cumulative flow
- Include distinct start and end total bars (often in a different color like blue or gray)
- Display running total labels on or near bars for clarity
- First and last bars typically represent totals, middle bars represent changes

## What a good version looks like

- A good version shows: a start total bar rising from zero, then one floating bar per change that begins where the previous running total ended and moves up for an increase or down for a decrease, and an end total bar rising from zero to the start plus all changes.
- A good version shows: connector lines from the end of each bar to the start of the next, so the running total can be followed across the chart.
- A good version shows: increases and decreases in a contrasting pair of semantic colors (such as green for gains and red for losses), and the start and end totals in a third, distinct color.
- A good version shows: a running total label on or near every bar, as the Notes ask, with a change bar's delta shown beside it if drawn, and the labels readable in both themes and not colliding with the connectors.
- A good version shows: the basic variant's single sequence of changes between one start and one end total, with no intermediate subtotal bars, second series or callouts.
- Expected, not a defect: floating bars that start partway up the value axis rather than at zero, and changes of very different size, including one that dwarfs the rest; floating is how the chart shows each change against the running total.
