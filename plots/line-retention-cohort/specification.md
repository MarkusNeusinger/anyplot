# line-retention-cohort: User Retention Curve by Cohort

## Description

A line chart showing the percentage of retained users over time since signup, with separate curves for different cohorts. All curves start at 100% at time zero and typically exhibit exponential decay, revealing how well a product retains users over their lifecycle. By overlaying multiple cohorts, teams can visually compare whether retention is improving or degrading across signup periods.

## Applications

- Product analytics teams comparing user retention across monthly or weekly signup cohorts to measure engagement trends
- A/B testing analysts evaluating how a new onboarding flow affects long-term user retention versus a control group
- Growth teams reporting retention improvements to stakeholders by showing cohort curves shifting upward over time

## Data

- `time_period` (numeric) - Time since signup in consistent units (days, weeks, or months), starting at 0
- `retention_rate` (numeric) - Percentage of users still active, ranging from 0 to 100, starting at 100% for all cohorts
- `cohort` (categorical) - Cohort label identifying the signup period (e.g., "Jan 2025", "Feb 2025")
- `cohort_size` (numeric) - Number of users in each cohort, displayed in the legend
- Size: 6-12 time periods per cohort, 3-6 cohorts
- Example: Monthly signup cohorts tracked weekly for 12 weeks, showing active user percentages

## Notes

- All curves must start at 100% at time zero
- Use distinct colors for each cohort with a legend showing cohort label and size (e.g., "Jan 2025 (n=1,245)")
- Y-axis should range from 0% to 100% with gridlines for easy reading
- X-axis represents time since signup, not calendar dates
- Consider using slightly decreasing opacity or thinner lines for older cohorts to emphasize recent ones
- A horizontal dashed reference line at a key retention threshold (e.g., 20%) can highlight target benchmarks

## What a good version looks like

- A good version shows: one curve per cohort, every curve starting at 100 percent at time zero, as the Notes require, and joining its retention values in order of time since signup.
- A good version shows: an x axis of time since signup in one consistent unit, not calendar dates, so the cohorts line up at equal age.
- A good version shows: a y axis running from 0 to 100 percent with gridlines, as the Notes ask, never cropped to the range the curves happen to occupy.
- A good version shows: a distinct color per cohort and a legend giving each cohort's label and size, as the Notes ask.
- A good version shows: the optional layers the Notes allow kept subordinate: older cohorts, if drawn fainter or thinner, still distinguishable in both themes, and a dashed threshold reference line, if drawn, behind the curves.
- Expected, not a defect: a steep early drop that flattens into a plateau, curves bunched together at the start and close to each other later, curves that cross, and newer cohorts whose curves end earlier than older ones.
