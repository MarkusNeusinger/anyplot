# bar-diverging: Diverging Bar Chart

## Description

A diverging bar chart displays bars extending in opposite directions from a central baseline, typically at zero. This visualization is ideal for comparing positive and negative values, showing responses above and below a neutral point, or contrasting opposing categories. Different colors distinguish positive from negative values, making it easy to identify magnitude and direction at a glance.

## Applications

- Visualizing survey responses (agree/disagree, satisfied/dissatisfied scales)
- Displaying net promoter scores or sentiment analysis results
- Comparing political polling data across ideological spectrums
- Showing profit/loss or growth/decline metrics across categories

## Data

- `category` (str) - Category label for each bar (e.g., product name, demographic group)
- `value` (float) - Numeric value that can be positive or negative
- Size: 5-30 categories works well; too many categories reduces readability
- Example: Survey responses with scores ranging from -100 to +100

## Notes

- Use contrasting colors for positive and negative values (e.g., blue/red, green/orange)
- Consider horizontal orientation for long category labels
- Add a vertical line or clear visual indicator at the zero baseline
- Sort bars by value to enhance pattern recognition

## What a good version looks like

- A good version shows: every bar starting at the zero baseline, positive values extending right (or up) and negative values left (or down), so bar length stays proportional to the magnitude, on a value axis that is never truncated.
- A good version shows: a clearly marked zero baseline, a line or an equivalent indicator across the full span of the bars, visible in both themes.
- A good version shows: one color for every positive bar and a contrasting one for every negative bar, so direction reads from color as well as from side.
- A good version shows: bars in order of value, so the chart runs from the largest positive value to the most negative one, with horizontal bars when category labels are long.
- Expected, not a defect: most bars on one side of zero, one side reaching much further than the other, and very short bars near zero; they show which way the data leans, not an imbalance to fix.
