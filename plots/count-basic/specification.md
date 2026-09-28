# count-basic: Basic Count Plot

## Description

A count plot displays the frequency of observations in each category of a categorical variable using vertical bars. Unlike a basic bar chart that requires pre-computed values, a count plot automatically counts occurrences from raw data. This makes it ideal for quick exploratory analysis of categorical distributions without manual aggregation.

## Applications

- Analyzing survey response distributions across multiple choice answers
- Visualizing the frequency of product categories in sales data
- Exploring class distributions in machine learning datasets before training

## Data

- `category` (categorical) - The categorical variable whose values will be counted
- Size: 3-20 unique categories recommended for readability
- Example: Survey responses (A/B/C/D), product types, customer segments, or any discrete categorical data

## Notes

- Bars should be sorted by frequency (descending) or kept in original/alphabetical order based on context
- Consider adding count labels on or above bars for precise reading
- Optional percentage annotations can show relative proportions
- Use consistent bar width and adequate spacing between categories

## What a good version looks like

- A good version shows: one vertical bar per category rising from a zero baseline to the number of observations in it, so bar height stays proportional to the count, on a count axis that is never truncated and has whole-number ticks.
- A good version shows: bars of one width with even gaps, and categories in the order the context calls for: by descending frequency, or their original or alphabetical order.
- A good version shows: count labels, if drawn, on or above their bars, and percentage annotations, if drawn, matching each bar's share of all observations, readable in both themes and not colliding with each other.
- A good version shows: the basic variant's single categorical variable: one color for all bars, the count and percentage labels the Notes allow, and no reference or mean lines, highlighted bars or bands, callouts, second grouping variable, stacking, error bars or cumulative line.
- Expected, not a defect: unequal heights, including one dominant category, a near-empty one and a long tail of rare categories; they are the point of the chart, not an imbalance to fix.
