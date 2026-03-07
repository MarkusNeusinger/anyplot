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
- Size: 8-12 cohorts with 8-12 periods each
- Example: Monthly signup cohorts from Jan 2024 to Oct 2024, with weekly retention percentages

## Notes

- Period 0 (signup period) should always show 100% retention for every cohort
- The heatmap should have a triangular shape: the first cohort has the most columns, each subsequent cohort has one fewer
- Use a sequential colormap from light (low retention) to dark (high retention), such as a green or blue gradient
- Display the retention percentage as text inside each cell
- Show cohort size (number of users) next to each cohort label on the y-axis
- X-axis labels should read "Week 0", "Week 1", etc. (or "Month 0", "Month 1" depending on the period granularity)
- Consider adding a color bar legend to indicate the retention scale
