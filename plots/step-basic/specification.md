# step-basic: Basic Step Plot

## Description

A step plot (also known as a stair plot or stepped line chart) displays data using horizontal lines connected by vertical lines, creating a stair-step pattern. Unlike line charts that interpolate between points, step plots show values as constant until the next change occurs. This makes them ideal for visualizing data that changes at discrete intervals, emphasizing the exact moments when values change.

## Applications

- Tracking cumulative sales or revenue over time where totals increase in discrete jumps
- Visualizing stock price changes or pricing tier adjustments throughout a trading day
- Displaying inventory levels that decrease or increase at specific events
- Showing digital signals, binary states, or step functions in engineering and mathematics

## Data

- `x` (numeric/datetime) - Sequential or time-based variable representing when changes occur
- `y` (numeric) - The value that remains constant until the next step
- Size: 10-100 data points work well; too many points may clutter the visualization
- Example: Monthly cumulative sales figures, hourly inventory snapshots

## Notes

- Use 'pre' step style when the value applies from the previous point until the current one
- Use 'post' step style when the value applies from the current point until the next one
- Use 'mid' step style to center the step between adjacent points
- Consider adding markers at data points to highlight where changes occur
- Grid lines can help readers trace values across the plot

## What a good version looks like

- A good version shows: the series drawn only as horizontal and vertical segments: each value held flat until the next change and each change drawn as a vertical jump, with no sloped or curved connections.
- A good version shows: steps that change at the data's x values with one step style for the whole series (pre, post or mid, chosen as the Notes describe to match when each value applies), and every flat segment at its exact y value.
- A good version shows: markers, if drawn as the Notes suggest, on the data points where changes occur and small enough that the flat segments still read as lines.
- A good version shows: the basic variant's single step line, with the data-point markers and grid lines the Notes allow, and no second series, fill under the steps, trend or smoothed line, reference or mean lines, highlighted segments, points or bands, or callouts.
- Expected, not a defect: jumps of very different height, plateaus of very different length, runs of repeated values that form one long flat segment, and the sharp corners themselves; none of them is to be smoothed.
