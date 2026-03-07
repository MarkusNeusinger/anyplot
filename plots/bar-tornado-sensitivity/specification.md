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
