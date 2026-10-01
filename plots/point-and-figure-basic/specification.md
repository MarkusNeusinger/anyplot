# point-and-figure-basic: Point and Figure Chart

## Description

A Point and Figure (P&F) chart is a price-action focused visualization that uses columns of X's (rising prices) and O's (falling prices) to display significant price movements while filtering out time and minor fluctuations. Unlike traditional time-based charts, P&F charts only plot a new symbol when price moves by a defined box size, and only start a new column when price reverses by a specified number of boxes (typically 3). This makes it ideal for identifying clear trends, support/resistance levels, and generating trading signals.

## Applications

- Identifying trend direction and strength in stock trading by observing the dominance of X columns (bullish) versus O columns (bearish)
- Detecting support and resistance levels where price repeatedly reverses, visible as horizontal price zones with multiple column reversals
- Calculating price targets using the traditional count methods based on column widths at breakout points
- Filtering out market noise in volatile markets to focus on meaningful price changes rather than time-based fluctuations

## Data

- `date` (datetime) - Trading dates for each price observation
- `high` (numeric) - High price for each period
- `low` (numeric) - Low price for each period
- `close` (numeric) - Closing price for each period (primary data for calculations)
- Box size: Fixed price increment that determines when a new X or O is added (e.g., $1, $2, or ATR-based)
- Reversal: Number of boxes required to start a new column in the opposite direction (default: 3)
- Size: 200-500 price observations over 6-12 months to generate meaningful patterns

## Notes

- Use X symbols for rising price columns and O symbols for falling price columns
- Green color for X columns (bullish) and red color for O columns (bearish) provides visual distinction
- Each column contains only X's or only O's - never mixed
- A new column starts only when price reverses by the reversal amount (e.g., 3 boxes)
- The X-axis represents columns (reversals), not time - this is a key feature of P&F charts
- Draw support trend lines connecting ascending lows (45-degree up) and resistance trend lines connecting descending highs (45-degree down)
- Box size significantly impacts chart appearance: smaller boxes show more detail, larger boxes emphasize major trends
- Consider adding a price scale on the Y-axis with grid lines at box size intervals

## What a good version looks like

- A good version shows: columns of X for rising and O for falling prices, as the Notes ask, every column holding one symbol only and neighboring columns alternating between X and O, the two also told apart by color where colored, green for X and red for O being the pair the Notes suggest.
- A good version shows: every symbol in its own box of a regular grid whose rows are one box size apart on the price axis, so stacked symbols stay separate glyphs and a column's top and bottom can be read as prices.
- A good version shows: a horizontal position that is construction, not time, as the Notes state: each column sits one even step to the right of the last, and a new column begins only where the price reversed by the reversal amount.
- A good version shows: support trend lines rising from lows and resistance trend lines falling from highs at the 45-degree slope the Notes ask for, one box per column, so on square boxes they run diagonally through the grid, leaving the symbols readable.
- A good version shows: the basic variant's X and O columns: besides the symbols, the price scale and box grid the Notes allow and the trend lines the Notes ask for, no price line or candles, volume panel, moving averages, other reference or mean lines, highlighted columns or bands, price targets, or callouts.
- Expected, not a defect: no time axis, columns of very different heights, many empty boxes, price levels revisited by several columns, and trend lines that cover only part of the chart.
