# flamegraph-basic: Flame Graph for Performance Profiling

## Description

A flame graph visualizes hierarchical call stack data from performance profiling, where each horizontal bar represents a function in the call stack and its width is proportional to the time (or samples) spent in that function. Stacks are layered bottom-to-top showing caller-to-callee relationships. Invented by Brendan Gregg, flame graphs are the standard visualization for identifying CPU bottlenecks and hot code paths across all major programming languages and profiling tools.

## Applications

- Analyzing CPU profiling data to identify performance bottlenecks in application code
- Visualizing memory allocation call stacks to find sources of excessive allocation
- Locating the hot code paths an optimization should target in a single profiling snapshot

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

## What a good version looks like

- A good version shows: one row of bars per stack depth with the root at the bottom, as the Notes ask, and every callee directly on top of its caller and within the caller's width.
- A good version shows: bar width proportional to the frame's share of the total samples or time, with siblings at the same depth directly adjacent and minimal or no gaps between them, as the Notes ask.
- A good version shows: a warm palette of yellows, oranges and reds, as the Notes ask, with adjacent frames still distinguishable, by hue variation or thin separators, in both themes.
- A good version shows: function names inside the bars wide enough to fit them, as the Notes ask, readable against the bar's fill in both themes and never spilling past their own bar.
- A good version shows: the basic variant's single profile: the stacked frames and their in-bar labels, axes, if drawn, that read as stack depth and as samples or time spent, never as a time sequence, and no second or differential profile, reference lines, highlighted frames or hot path, or callouts.
- Expected, not a defect: many narrow unlabeled frames, towers of very different height with a ragged top edge, flat stretches where a frame has nothing above it, and a left-to-right order that means nothing.
