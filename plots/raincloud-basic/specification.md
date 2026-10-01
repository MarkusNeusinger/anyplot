# raincloud-basic: Basic Raincloud Plot

## Description

A raincloud plot combines three visualization elements—a half-violin (the "cloud"), jittered strip points (the "rain"), and a box plot—to provide a comprehensive view of data distribution. This hybrid approach shows distribution shape, summary statistics, and individual observations simultaneously, addressing the limitation of box plots that can hide multimodal distributions. Often called the "gold standard" for transparent statistical visualization in scientific publications.

## Applications

- Comparing treatment effects across experimental groups in clinical trials
- Visualizing response time distributions in psychology experiments
- Analyzing score distributions across different conditions in A/B testing
- Presenting survey response distributions by demographic groups

## Data

- `category` (categorical) - Group labels for comparison on the categorical axis
- `value` (numeric) - Continuous variable values shown on the value axis
- Size: 20-300 observations per category, 2-6 categories
- Example: Reaction times (ms) for control vs treatment groups

## Notes

- **Required Orientation**: Use HORIZONTAL orientation with categories on y-axis and values on x-axis. "Above" and "below" always refer to the y-direction (screen up/down), not the x-direction
- **Critical Layout**: For each category on the y-axis: the "cloud" (half-violin/KDE) must extend ABOVE the category baseline (upward on screen), the boxplot sits centered ON the category baseline, and "rain" (jittered points) must appear BELOW the category baseline (downward on screen) - like rain falling from a cloud
- Clip the violin to show only half (the "cloud" portion), not a full violin
- Use moderate jitter (0.05-0.1) to spread rain points without excessive overlap
- Apply transparency (alpha 0.5-0.7) to jittered rain points for visibility
- Include median and quartile markers in box plot
- The visual metaphor must be clear: cloud rises upward (positive y-direction), rain falls downward (negative y-direction) from each category line

## What a good version looks like

- A good version shows: the horizontal orientation the Notes require, with the categories on the y axis and the values on the x axis.
- A good version shows: for each category a half violin (the cloud) rising upward from the category baseline, a box plot with median and quartile markers centered on the baseline, and jittered points (the rain) below the baseline, as the Notes require.
- A good version shows: the cloud clipped to a single half with its flat edge along the baseline, as the Notes ask, and each category's cloud and rain staying clear of the neighboring categories' marks.
- A good version shows: every rain point at its value on the value axis, translucent and spread only up and down by a moderate jitter, as the Notes ask, so the rain forms a narrow band under its box.
- A good version shows: the basic variant's cloud, box and rain for each category, and, besides these three, no mean markers, reference or mean lines, lines connecting categories, highlighted categories or bands, or callouts.
- Expected, not a defect: lumpy, skewed or multimodal clouds of different height, rain points that overlap where values are dense, jitter offsets that are layout rather than data, a box whose upper half covers the foot of its cloud, and points beyond the whiskers.
