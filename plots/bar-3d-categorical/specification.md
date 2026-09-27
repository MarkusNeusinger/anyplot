# bar-3d-categorical: 3D Bar Chart for Categorical Comparison

## Description

A three-dimensional bar chart where bars rise from a 2D categorical grid, with height encoding the measured value. Two categorical axes define the grid position on the base plane while the vertical axis shows magnitude. This visualization extends the bar chart family into 3D space, making it effective for comparing values across two categorical dimensions simultaneously.

## Applications

- Comparing sales figures across product categories and geographic regions simultaneously
- Displaying survey responses across two demographic dimensions (e.g., age group vs education level)
- Showing experimental results with two categorical factors in factorial designs
- Visualizing frequency tables or cross-tabulations with two grouping variables

## Data

- `x_category` (str) - first categorical dimension (e.g., product type, region)
- `y_category` (str) - second categorical dimension (e.g., time period, segment)
- `value` (float) - bar height representing the measured quantity
- Size: 3-10 categories per axis, forming a grid of 9-100 bars

## Notes

- Bars should have slight spacing between them for visual clarity and depth perception
- Color can encode the value magnitude or a third categorical variable
- Viewing angle should be adjustable; a default elevation of ~30 degrees and azimuth of ~45 degrees provides good readability
- Grid lines on the base plane help relate bars to their categorical positions
- Consider adding value labels on top of bars when the grid is small (under 25 bars)
- A color bar or legend should indicate the mapping when color encodes a variable

## What a good version looks like

- A good version shows: one bar per pair of categories standing on its cell of the base-plane grid, its height above the base plane proportional to its value, read against a vertical value axis that starts at zero and has readable ticks.
- A good version shows: an elevated oblique view, as the Notes suggest, that shows the base-plane grid, both categorical axes with their labels and the value axis, with slight gaps between bars so their faces and depth read.
- A good version shows: where taller front bars hide rear ones, an oblique view angle and bar spacing that keep the tops of the rear bars and the value axis in sight, so a fully hidden bar is the exception rather than the rule.
- A good version shows: color, if used, encoding either the value or a third categorical variable, with a color bar or legend that says which.
- A good version shows: value labels, if drawn on a small grid, on top of their own bar, readable in both themes and not colliding with each other.
- Expected, not a defect: rear bars partly hidden behind taller front ones, and perspective foreshortening that makes bars further back look smaller; both are inherent to the 3D view.
