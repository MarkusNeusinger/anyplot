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

## What a good version looks like

- A good version shows: two cumulative areas on a price x-axis, bids to the left and asks to the right, each accumulating from the best price nearest the mid price outward, as the Notes ask, so both curves are lowest at the center and never fall as they move away from it.
- A good version shows: both areas as step curves rather than smooth lines, as the Notes ask, with every step at its price level and every plateau at its cumulative quantity.
- A good version shows: the bid area in green and the ask area in red, with semi-transparent fills and matching solid outlines, as the Notes ask, distinguishable in both themes.
- A good version shows: the bid-ask spread left as a visible empty gap at the center, as the Notes ask; the dashed mid price line and the mid price and spread annotation the Notes allow, if drawn, sit at that gap and leave the areas uncovered.
- A good version shows: a y-axis that starts at zero and an x-axis centered on the mid price, as the Notes ask, so the two mirrored areas look roughly balanced.
- Expected, not a defect: tall single steps where a large order rests, two sides that end at different heights, steps of uneven width and height, a spread that is narrow against the price range shown, and empty space above the curves near the center.
