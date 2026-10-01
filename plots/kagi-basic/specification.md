# kagi-basic: Basic Kagi Chart

## Description

A Kagi chart is a Japanese charting technique that displays price movements using vertical lines of varying thickness. Unlike time-based charts, Kagi charts change direction only when price moves by a significant amount (the reversal threshold), effectively filtering out market noise. Thick lines (yang) indicate uptrends when price exceeds previous highs, while thin lines (yin) show downtrends when price falls below previous lows, making trend identification intuitive.

## Applications

- Identifying clear trend reversals in stock trading by observing when thick lines transition to thin lines or vice versa
- Analyzing currency pair movements in forex markets where filtering out minor fluctuations helps spot major trend changes
- Evaluating cryptocurrency price action over extended periods by focusing on significant price movements rather than time-based volatility

## Data

- `date` (datetime) - The timestamp when each price point was recorded
- `close` (numeric) - Closing price or last traded price at each timestamp
- Reversal amount: A fixed price or percentage threshold that triggers a direction change (e.g., $2 or 4%)
- Size: 100-500 price observations to generate meaningful trend patterns
- Example: Daily closing prices for a stock over 6-12 months with a 4% reversal threshold

## Notes

- Use thick lines for yang (bullish) segments and thin lines for yin (bearish) segments
- Direction changes occur only when price moves by the reversal amount in the opposite direction
- Horizontal segments (shoulders and waists) mark the points where trend direction changes
- Green color for yang (thick/up) and red color for yin (thin/down) provides visual clarity
- X-axis typically shows line index rather than time since Kagi charts are time-independent
- The reversal threshold significantly impacts chart appearance - smaller values show more detail, larger values emphasize major trends

## What a good version looks like

- A good version shows: one unbroken line of vertical segments joined by short horizontal segments at the shoulders and waists, as the Notes describe, each vertical segment running between the price levels at which the direction turned, read on the price axis.
- A good version shows: thick lines for yang and thin lines for yin, as the Notes ask, clearly different in weight in both themes, the line turning thick where it rises above the previous shoulder and thin where it falls below the previous waist.
- A good version shows: color that agrees with the thickness at every point where the two states are colored, green for yang and red for yin being the pair the Notes suggest; a single-color line relies on thickness alone to tell them apart.
- A good version shows: a horizontal position that is construction, not time: the line steps one even column to the right only where the price reversed by the reversal amount, on an x-axis that shows a line index or irregular dates.
- A good version shows: the basic variant's single Kagi line: besides its thick and thin segments and its shoulders and waists, no underlying price line or candles, volume panel, moving averages, trend, reference or mean lines, highlighted segments or bands, buy or sell signals, or callouts.
- Expected, not a defect: no regular time axis, far fewer segments than price observations, vertical segments of very different lengths, long runs in one thickness, and a last segment that is still open.
