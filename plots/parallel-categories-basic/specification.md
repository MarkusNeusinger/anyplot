# parallel-categories-basic: Basic Parallel Categories Plot

## Description

A parallel categories plot visualizes categorical data across multiple dimensions, with vertical axes representing each categorical variable and ribbons connecting categories to show observation flow. Unlike parallel coordinates (which use lines for numeric data), parallel categories use width-proportional ribbons to show counts or frequencies, making it ideal for understanding how categorical values co-occur and flow across multiple classification dimensions.

## Applications

- Analyzing customer journey paths from acquisition channel through product category to purchase outcome
- Visualizing survey response patterns across multiple demographic or preference questions
- Exploring classification results showing predicted vs actual categories with feature breakdowns
- Understanding multi-stage process flows like support ticket routing through departments

## Data

- `dimension_1` through `dimension_n` (categorical) - Multiple categorical variables for each observation
- `count` (numeric, optional) - Observation count or weight for aggregated data
- Size: 3-6 categorical dimensions, each with 2-8 unique values
- Example: Titanic survival data with class, sex, age group, and survival status

## Notes

- Ribbon width should be proportional to observation count or frequency
- Color by first dimension (source) or last dimension (outcome) for clarity
- Interactive highlighting helps trace paths through multiple categories
- Consider ordering categories within each dimension to minimize ribbon crossings
- Too many categories per dimension reduces readability; aggregate rare values if needed

## What a good version looks like

- A good version shows: one parallel axis per categorical dimension, named, and divided into one labeled segment per category whose length is that category's share of the observations.
- A good version shows: ribbons between neighboring axes, each with a width proportional to the count or frequency of the observations that share the categories it connects, as the Notes ask.
- A good version shows: ribbons colored by the categories of one dimension, the first or the last, as the Notes ask, keeping that color across every axis, with a legend or the colored segments saying which dimension it is.
- A good version shows: category order within an axis set by the layout, not by data: a natural order or the crossing-reducing order the Notes suggest; only segment lengths and ribbon widths carry counts.
- A good version shows: the basic variant's axes, category segments and ribbons: besides their labels and the interactive path highlighting the Notes mention, no path singled out in the static image, reference lines, callouts, numeric axis or second panel.
- Expected, not a defect: ribbons that cross, a dense braid toward the later axes as ribbons split by category, hair-thin ribbons for rare combinations, segments of very unequal length, and rare categories merged into one segment.
