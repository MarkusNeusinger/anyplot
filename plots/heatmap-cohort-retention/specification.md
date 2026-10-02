# heatmap-cohort-retention: Cohort Retention Heatmap

## Description

A triangular heatmap displaying user retention rates across signup cohorts and time periods. Each row represents a cohort (e.g., users who signed up in a specific month), each column represents periods since signup, and cell color intensity indicates the retention percentage. The triangular shape naturally emerges because more recent cohorts have fewer elapsed periods. This visualization reveals retention trends, highlights churn patterns, and enables comparison of cohort quality over time.

## Applications

- SaaS product analytics: tracking weekly or monthly user retention to measure feature stickiness and identify engagement drops
- Mobile app growth: comparing retention curves across acquisition channels or app versions to optimize onboarding
- Subscription business monitoring: identifying seasonal churn patterns and evaluating the impact of retention interventions
- Gaming analytics: measuring player return rates across cohorts to assess content update effectiveness

## Data

- `cohort` (string) - Cohort label representing the signup period (e.g., "Jan 2024", "Feb 2024")
- `period` (integer) - Number of periods since signup (0, 1, 2, ...), where period 0 is the signup period
- `retention_rate` (float) - Percentage of users retained, ranging from 0 to 100; period 0 is always 100%
- `cohort_size` (integer) - Number of users in each cohort (displayed alongside cohort labels)
- Size: 8-12 cohorts; the first cohort has 8-12 periods and each later cohort fewer
- Example: Monthly signup cohorts from Jan 2024 to Oct 2024, with monthly retention percentages

## Notes

- Period 0 (signup period) should always show 100% retention for every cohort
- The heatmap should have a triangular shape: the first cohort has the most columns, each subsequent cohort has one fewer
- Use a sequential colormap from light (low retention) to dark (high retention), such as a green or blue gradient
- Display the retention percentage as text inside each cell
- Show cohort size (number of users) next to each cohort label on the y-axis
- X-axis labels should read "Week 0", "Week 1", etc. (or "Month 0", "Month 1" depending on the period granularity)
- Consider adding a color bar legend to indicate the retention scale

## What a good version looks like

- A good version shows: a row per signup cohort and a column per period since signup, each cell at its cohort and period, with the period labels the Notes ask for (week or month numbers) on the x axis.
- A good version shows: the triangular shape the Notes ask for, the first cohort with the most cells and each later cohort with fewer, the remaining positions left empty instead of filled with zeros or a color from the scale.
- A good version shows: a sequential colormap running from light for low retention to dark for high, as the Notes ask; a color bar, if drawn, shows the retention scale.
- A good version shows: the retention percentage as text inside every cell, as the Notes ask, legible against light and dark cells alike in both themes, with the signup period reading 100 percent for every cohort.
- A good version shows: each cohort's size next to its cohort label on the y axis, as the Notes ask.
- Expected, not a defect: the empty triangle beyond the staircase edge, a uniform dark signup column, a steep drop right after signup followed by a slow decline, and cohorts that differ in level.
