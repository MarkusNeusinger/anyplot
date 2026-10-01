# range-interval: Range Interval Chart

## Description

A range interval chart displays min-max ranges or intervals as vertical or horizontal bars/segments for each category, making it ideal for visualizing uncertainty bounds, confidence intervals, or value spreads. Unlike error bars which extend from a central data point, range intervals show the full span between two values as a filled bar or line segment, emphasizing the range itself rather than deviation from a center. This visualization excels at comparing ranges across multiple categories simultaneously.

## Applications

- Displaying temperature ranges (daily high/low) across months or locations
- Comparing salary ranges by job title or department
- Showing confidence intervals for statistical estimates across groups
- Visualizing stock price ranges (high/low) over multiple periods

## Data

- `category` (categorical) - Labels for each range group
- `min_value` (numeric) - Lower bound of the range/interval
- `max_value` (numeric) - Upper bound of the range/interval
- Size: 5-25 categories for optimal readability
- Example: Monthly temperature ranges with minimum and maximum values per month

## Notes

- Use horizontal orientation when category labels are long
- Sort categories by range size, midpoint, or logical order (e.g., chronological)
- Consider adding markers at min/max endpoints for emphasis
- Semi-transparent fill or distinct colors help differentiate overlapping ranges
- Optional: show midpoint markers or reference lines for context

## What a good version looks like

- A good version shows: one bar or line segment per category spanning exactly from its minimum to its maximum value on a shared value axis, floating between the two bounds rather than anchored at zero, so the span itself is the mark.
- A good version shows: ranges of one thickness with even spacing, in an order the Notes ask for: by range size, by midpoint or a logical order such as chronological, and drawn horizontally when category labels are long.
- A good version shows: both ends of every range readable against the page in both themes, with markers at the minimum and maximum, if drawn as the Notes allow, sitting exactly on the two bounds.
- A good version shows: each range distinguishable from its neighbors, with a semi-transparent fill or distinct colors, as the Notes suggest, where ranges would otherwise cover each other.
- A good version shows: midpoint markers and reference lines, if drawn as the Notes allow, kept subordinate to the ranges, with each midpoint marker at the middle of its own range.
- Expected, not a defect: ranges of very different length, including a very short one, ranges whose spans overlap along the value axis, and a value axis that does not start at zero, because the bounds, not a length from zero, carry the values.
