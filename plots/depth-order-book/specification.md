# depth-order-book: Order Book Depth Chart

## Description

A market depth chart visualizes a snapshot of an exchange order book as two cumulative step areas around the mid price. Cumulative bid volume rises as a green step area to the left of the mid price (summing buy orders from the best bid downward), while cumulative ask volume rises as a red step area to the right (summing sell orders from the best ask upward). The bid-ask spread appears as a gap at the center, with price on the x-axis and cumulative quantity on the y-axis. This is the iconic chart found in nearly every trading and crypto exchange UI, revealing liquidity, support/resistance walls, and the imbalance between buying and selling pressure.

## Applications

- Assessing liquidity and slippage risk before placing a large market order on a crypto or equities exchange
- Spotting large "walls" of resting limit orders that may act as short-term support or resistance levels
- Comparing buy-side versus sell-side pressure to gauge near-term directional bias around the mid price

## Data

- `price` (numeric) - Price level of each order book entry, on the x-axis
- `quantity` (numeric) - Resting order size (volume) available at that price level
- `side` (categorical) - Whether the level is a `bid` (buy) or `ask` (sell)
- Derived `cumulative_quantity` (numeric) - Running sum of quantity from the mid price outward, plotted on the y-axis
- Size: 20-100 price levels per side
- Example: A single order-book snapshot for a BTC/USD pair, with ~50 bid levels below and ~50 ask levels above a mid price near 60,000

## Notes

- Compute cumulative quantity separately per side, accumulating from the best bid/best ask (nearest the mid price) outward toward worse prices
- Render both areas as left-continuous step (staircase) curves, not smooth lines, to reflect discrete price levels
- Use green for the bid area and red for the ask area, with semi-transparent fills and matching solid outline strokes
- Leave the bid-ask spread as a visible empty gap at the center; optionally draw a dashed vertical line at the mid price and annotate the mid price and spread value
- The y-axis starts at zero; the x-axis is centered so the mirrored areas are roughly balanced visually
- Derive a plausible static snapshot synthetically (e.g. quantities drawn from a distribution that grows away from the mid price) — no live feed is required
