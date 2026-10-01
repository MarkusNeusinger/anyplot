# dot-matrix-proportional: Dot Matrix Chart for Proportional Counts

## Description

A dot matrix chart displays proportions using a grid of equally-sized dots where filled or colored dots represent counts out of a total. Each dot corresponds to one unit, making it intuitive to read "X out of N" statistics at a glance. Unlike waffle charts that use percentage-based squares, dot matrix charts emphasize absolute counts with variable grid sizes, excelling at risk communication and survey result visualization.

## Applications

- Showing survey results where 47 out of 100 respondents agreed with a statement
- Visualizing medical risk such as 3 in 1,000 patients experiencing a side effect
- Displaying election or vote breakdowns across candidates or parties
- Communicating proportions in infographics and reports for general audiences

## Data

- `category` (str) - Group name identifying each segment (e.g., "Agreed", "Disagreed", "No opinion")
- `count` (int) - Number of units (dots) for that category
- `total` (int) - Total grid size representing the full population (e.g., 100, 500, 1000)
- Size: 2-5 categories, total between 50 and 1,000 dots

## Notes

- Grid layout should match the total (e.g., 10x10 for 100, 10x50 for 500)
- Each dot represents exactly one unit
- Dots are color-coded by category, filled left-to-right, top-to-bottom
- Include a legend with category labels and their counts
- Use uniform dot size and spacing for accurate visual comparison
- Consider adding count or percentage annotations alongside the legend

## What a good version looks like

- A good version shows: a grid with exactly as many dots as the total, one dot per unit, laid out to match the total as the Notes ask; a dot's position is layout, not data, so there are no axes or grid lines.
- A good version shows: dots of one size with even spacing in both directions, as the Notes ask, so equal counts cover equal areas and every dot is visible against the page in both themes.
- A good version shows: each category's dots in its own color and equal in number to its count, filled left to right and top to bottom as the Notes ask, so each category forms one run of dots that can be read as a count out of the total.
- A good version shows: a legend with each category's label and its count, as the Notes ask; count or percentage annotations beside it, if drawn, match the dots.
- A good version shows: dots that belong to no listed category, if the total has any, in the grid as a neutral remainder rather than left out.
- Expected, not a defect: runs of very different length, including a category of only a few dots among hundreds, a run that ends partway through a row, a last row that is incomplete when the total does not fill it, and small dots when the total is large.
