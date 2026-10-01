# drawdown-basic: Drawdown Chart

## Description

A drawdown chart visualizes the percentage decline from peak value over time, showing how far an investment or asset has fallen from its highest point. This chart is essential for risk assessment and understanding the magnitude of losses during unfavorable market periods. The filled area below the zero line emphasizes the depth and duration of drawdowns, making it easy to identify maximum drawdown periods and recovery points.

## Applications

- Risk management analysis to identify maximum drawdown periods and evaluate worst-case scenarios
- Portfolio performance evaluation comparing drawdown characteristics across different assets or strategies
- Investment decision-making by visualizing historical recovery times and drawdown frequencies
- Trading strategy assessment to understand downside risk and volatility patterns

## Data

- `date` (datetime) - Trading dates or time periods
- `price` or `value` (numeric) - Asset price, portfolio value, or cumulative returns
- Size: 250-1500 data points (1-5 years of daily data)
- Example: Daily closing prices of a stock or portfolio NAV over multiple years

## Notes

- Calculate drawdown as percentage decline from the running maximum: `(value - running_max) / running_max * 100`
- Fill the area from the drawdown line to zero baseline with a semi-transparent color (typically red)
- Highlight the maximum drawdown period with a distinct marker or annotation
- Indicate recovery points where drawdown returns to zero (new highs)
- Display key statistics: maximum drawdown percentage, max drawdown duration, and recovery time
- Zero line should be clearly visible as the reference baseline
- Consider using a secondary y-axis or annotation to show the underlying price/value series

## What a good version looks like

- A good version shows: the drawdown as a percentage decline from the running maximum, a curve that stays at or below zero at every date and touches zero only at new highs, with zero at the top of its axis and deeper losses further down.
- A good version shows: a semi-transparent fill between the curve and the zero baseline in a loss color such as red, as the Notes ask, with the zero line clearly visible in both themes.
- A good version shows: the maximum drawdown highlighted with a distinct marker or annotation at its trough, and recovery points marked where the curve returns to zero, as the Notes ask.
- A good version shows: the key statistics the Notes ask for (maximum drawdown percentage, its duration and the recovery time) as text that matches the curve and stays clear of it.
- A good version shows: the basic variant's single drawdown series: besides the zero baseline, the highlight, recovery markers and statistics the Notes ask for and the underlying value series the Notes allow, no second asset, other reference or mean lines, highlight bands on other periods, or further callouts.
- Expected, not a defect: a last drawdown still open at the end of the window, so its recovery is reported as not yet reached, long flat stretches at zero during runs of new highs, sharp drops followed by slow climbs, and many shallow dips.
