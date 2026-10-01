# dumbbell-basic: Basic Dumbbell Chart

## Description

A dumbbell chart (also called a connected dot plot or Cleveland dot plot) compares two values for each category by displaying two dots connected by a line. It effectively visualizes differences, changes, or ranges between two data points such as before/after comparisons, gaps, or min/max values. The connected dots make it easy to see both the magnitude and direction of change.

## Applications

- Before/after performance comparisons (e.g., test scores before and after training)
- Gap analysis between groups (e.g., salary differences by department or gender)
- Comparing metrics between two time periods (e.g., Q1 vs Q4 sales by region)
- Displaying ranges such as minimum and maximum values per category

## Data

- `category` (string) - Labels for each comparison group
- `start_value` (numeric) - The first/left data point value
- `end_value` (numeric) - The second/right data point value
- Size: 5-20 categories for optimal readability
- Example: Employee satisfaction scores before and after policy changes

## Notes

- Horizontal orientation preferred with categories on y-axis and values on x-axis
- Use distinct colors for start and end dots to differentiate the two values
- Sort by difference or one of the values to reveal patterns
- Connecting line should be thin and subtle to not overpower the dots

## What a good version looks like

- A good version shows: two dots per category, one at its start value and one at its end value on a shared value axis, joined by a straight line that spans exactly the gap between them, with no dot moved off its value.
- A good version shows: start dots in one color and end dots in another, as the Notes ask, the same pair in every row, told apart in both themes and named in a legend or by direct labels.
- A good version shows: a connecting line that is thin and subtle, as the Notes ask, so the dots dominate, while it stays visible against the page in both themes.
- A good version shows: categories sorted by the difference or by one of the two values, as the Notes ask, in the horizontal layout the Notes prefer, with categories on the vertical axis, unless the scenario calls for a vertical one.
- A good version shows: the basic variant's two dots and one connecting line per category, and no third value per row, reference or mean lines, highlighted rows or bands, trend lines, error bars, or callouts beyond plain value or difference labels.
- Expected, not a defect: gaps of very different length, a row whose two dots nearly coincide, rows whose change runs against the others, and a value axis that does not start at zero, because dot position, not length from zero, carries the values.
