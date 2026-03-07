# flamegraph-basic: Flame Graph for Performance Profiling

## Description

A flame graph visualizes hierarchical call stack data from performance profiling, where each horizontal bar represents a function in the call stack and its width is proportional to the time (or samples) spent in that function. Stacks are layered bottom-to-top showing caller-to-callee relationships. Invented by Brendan Gregg, flame graphs are the standard visualization for identifying CPU bottlenecks and hot code paths across all major programming languages and profiling tools.

## Applications

- Analyzing CPU profiling data to identify performance bottlenecks in application code
- Visualizing memory allocation call stacks to find sources of excessive allocation
- Comparing before/after profiling snapshots during performance optimization work

## Data

- `function` (string) - Name of the function in the call stack
- `stack` (string) - Semicolon-delimited call stack path from root to leaf (e.g., `main;process;compute`)
- `value` (numeric) - Number of samples or time units spent in this stack frame
- Size: 50-500 unique stack traces
- Example: Simulated CPU profiling data with nested function call hierarchies and sample counts

## Notes

- Each row of stacked bars represents a depth level in the call stack, with the root at the bottom
- Bar width encodes the proportion of total samples, not execution order (x-axis ordering is alphabetical or arbitrary, not temporal)
- Use a warm color palette (yellows, oranges, reds) following the conventional flame graph aesthetic
- Bars should be directly adjacent with minimal or no gaps between siblings at the same stack depth
- Include function name labels inside bars when the bar is wide enough to fit the text
