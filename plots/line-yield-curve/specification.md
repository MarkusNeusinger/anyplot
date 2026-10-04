# line-yield-curve: Yield Curve (Interest Rate Term Structure)

## Description

A yield curve plots interest rates (yields) of bonds against their maturities, from short-term (e.g., 1 month) to long-term (e.g., 30 years). It is one of the most iconic charts in macroeconomics and finance, used to assess market expectations for future interest rates, economic growth, and inflation. An inverted yield curve (where short-term rates exceed long-term rates) is a widely followed recession indicator. The plot should support displaying multiple curves (e.g., different dates) on the same axes to show how the term structure evolves over time.

## Applications

- Comparing U.S. Treasury yield curves across different dates to track monetary policy shifts and recession signals
- Visualizing the term structure of government bonds for central bank publications and financial media
- Analyzing spread compression or inversion between short-term and long-term maturities for investment strategy decisions

## Data

- `maturity` (string) - Bond maturity label (e.g., "1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y")
- `maturity_years` (float) - Numeric maturity in years for proper x-axis spacing (e.g., 0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30)
- `yield_pct` (float) - Annualized yield in percent (e.g., 4.25, 3.80)
- `date` (string) - Date of the yield curve snapshot for multi-curve comparison (e.g., "2024-01-15")
- Size: 11 maturities per curve, 2-3 curves for comparison, at least one of them inverted
- Example: U.S. Treasury yield curve data showing a normal curve, a flat curve, and an inverted curve on different dates

## Notes

- Use `maturity_years` for x-axis positioning to reflect true time spacing (log or linear scale); use `maturity` labels for tick marks
- Include at least two curves on the same plot to show how the yield curve shape changes over time (e.g., a normal upward-sloping curve vs. an inverted curve)
- Highlight the inversion region where short-term yields exceed long-term yields using shading or annotation
- Use a clean, professional style consistent with financial publications (minimal gridlines, muted colors)
- Add a legend indicating the date for each curve

## What a good version looks like

- A good version shows: every curve as a line through its yields in order of maturity, each point at its maturity in years on a linear or log axis, as the Notes ask, so the distance between maturities reflects time rather than even category spacing, and never smoothed away from its points.
- A good version shows: tick marks labeled with the maturity labels, as the Notes ask, each at the position of its maturity.
- A good version shows: at least two curves on the same axes, as the Notes ask, distinguishable in both themes, with a legend that gives the date of each curve.
- A good version shows: the inversion region, where short-term yields exceed long-term yields, highlighted by shading or an annotation, as the Notes ask, without hiding the curves.
- A good version shows: a yield axis in percent that spans all curves, with the minimal gridlines the Notes ask for staying behind them.
- Expected, not a defect: short maturities bunched together at the left of a linear axis, unevenly spaced ticks, curves that cross or sit far apart in level, a nearly flat curve, and a hump or kink at a single maturity.
