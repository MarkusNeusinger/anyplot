# pyramid-basic: Basic Pyramid Chart

## Description

A pyramid chart displays two opposing horizontal bar charts that share a central axis, creating a pyramid or butterfly shape. This visualization is ideal for comparing two related metrics across the same categories, revealing asymmetries and patterns in bidirectional data. Most commonly used for population pyramids showing age-gender distributions.

## Applications

- Population demographics showing age distribution by gender
- Survey analysis comparing agree vs disagree responses
- Before/after comparisons across categories
- Market research comparing two competing products or segments

## Data

- `category` (categorical) - Shared categories for central axis (e.g., age groups)
- `value_left` (numeric) - Values for left-extending bars
- `value_right` (numeric) - Values for right-extending bars
- Size: 5-15 categories typical
- Example: Age groups with male and female population counts

## Notes

- Left bars extend from center to the left, right bars extend from center to the right
- Both sides should use symmetric axis scales for fair comparison
- Use distinct colors for each side (e.g., blue/pink for gender)
- Category labels should be placed along the central axis
- Include legend or title identifying what each side represents

## What a good version looks like

- A good version shows: each category as a pair of horizontal bars extending in opposite directions from one shared central axis, left values to the left and right values to the right, each bar's length proportional to its value.
- A good version shows: one symmetric scale for both sides, so equal distances from the center mean equal amounts, with tick labels showing magnitudes on both sides rather than negative numbers on the left.
- A good version shows: one distinct color per side, used for every bar on that side, and a legend or title naming what each side represents.
- A good version shows: categories in a meaningful order along the central axis, their natural order when they have one (age groups ascending from bottom to top), with each category's label level with its pair of bars.
- A good version shows: the basic variant's two mirrored series only, with no overlaid comparison outline, stacked sub-groups, share annotations or callouts.
- Expected, not a defect: the two sides differing in length and a silhouette that bulges, narrows or tapers unevenly; the asymmetry between the sides is what the chart exists to reveal.
