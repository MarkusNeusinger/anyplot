# bubble-packed: Basic Packed Bubble Chart

## Description

A packed bubble chart displays data as circles where size represents value, and circles are packed together without overlap using physics simulation. Unlike scatter or traditional bubble charts, position has no meaning - only size and optional grouping matter. This visualization efficiently uses space for comparing values across many categories.

## Applications

- Budget and spending visualization: comparing department expenditures where circle size shows amount
- Market share comparison: visualizing competitor sizes within an industry
- Portfolio composition: displaying asset allocation or inventory breakdown
- Categorical value comparison: showing values across many categories where ranking and proportion matter

## Data

- `label` (categorical) - Category or item names
- `value` (numeric) - Size values determining circle area
- `group` (categorical, optional) - For clustering related items together
- Size: 10-100 items recommended for clear visualization
- Example: Synthetic data representing category values

## Notes

- Scale circle sizes by area (not radius) for accurate visual perception
- Use force simulation to pack circles without overlap
- Labels can be placed inside circles (if large enough) or as tooltips
- Color can encode category or group membership
- Optional grouping clusters related circles with spacing between groups

## What a good version looks like

- A good version shows: one circle per item whose area, not radius, is proportional to its value, as the Notes ask, so a value twice as large has twice the area.
- A good version shows: circles packed into one compact cluster, or one cluster per group where the grouping the Notes allow is used, touching or nearly touching and none crossing another, as the Notes ask; position comes from the packing, not from data, so no axes or grid.
- A good version shows: color, if it encodes category or group membership as the Notes allow, identified by a legend or by labels, with every circle visible against the page in both themes.
- A good version shows: grouping, if used, as clusters of related circles with spacing between the groups, as the Notes allow.
- A good version shows: labels, if placed inside circles, only in circles large enough to hold them, as the Notes allow, readable against the fill in both themes and not colliding with a neighbor's label.
- Expected, not a defect: circles of very different size, small unlabeled ones, small gaps between circles, and an irregular cluster outline with empty canvas corners, since circles cannot tile a rectangle.
