# bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis

## Description

A horizontal bar chart where bars are sorted by influence magnitude, extending left and right from a base case vertical reference line. Each bar represents one input parameter and shows how varying that parameter between its low and high values affects the output, creating a characteristic tornado shape (widest bars at top, narrowest at bottom). Dual colors distinguish low-input from high-input effects, making it immediately clear which parameters drive the most uncertainty.

## Applications

- Financial modeling: identifying which assumptions (discount rate, growth rate, costs) most affect net present value
- Risk analysis: performing one-way sensitivity analysis to rank uncertainty drivers in project cost or schedule estimates
- Engineering design: determining which design parameters have the greatest impact on system performance
- Consulting and stakeholder communication: presenting sensitivity results in an intuitive, ranked format

## Data

- `parameter` (str) - Name of the input variable being varied (e.g., "Discount Rate", "Material Cost")
- `low_value` (float) - Output result when the parameter is set to its low scenario value
- `high_value` (float) - Output result when the parameter is set to its high scenario value
- `base_value` (float) - Output result at the base case (single value used as the center reference line)
- Size: 6-15 parameters recommended for readability; bars sorted by total range (high - low) descending
- Example: NPV sensitivity analysis with 8-10 financial assumptions varied one at a time

## Notes

- Draw a vertical reference line at the base case value
- Sort bars by total range (|high_value - low_value|) with the widest bar at the top
- Use two distinct colors: one for the low-scenario side and one for the high-scenario side
- Label each bar with the parameter name on the y-axis
- Optionally display the low/high input values or resulting output values at bar ends
- The x-axis represents the output metric (e.g., NPV, cost, duration)

## What a good version looks like

- A good version shows: one horizontal bar per parameter spanning from its low-scenario to its high-scenario result, split by a vertical base-case reference line, with the widest range at the top and narrower ones below, so the stack tapers into a tornado.
- A good version shows: one color for the low-scenario segment and a distinct one for the high-scenario segment, applied by scenario on every bar, whichever side of the base case a segment falls on, and identified in a legend.
- A good version shows: the base-case line visible in both themes across all bars, each parameter name beside its bar on the category axis, and the output metric with its units on the value axis.
- A good version shows: low and high values at the bar ends, if drawn, clear of the bars, the base-case line and the parameter names, readable in both themes.
- Expected, not a defect: bars that reach unequally to the two sides of the base case, a value axis that does not start at zero, and a parameter whose low-scenario result lies above the base case, which puts its low-scenario color on the right.
