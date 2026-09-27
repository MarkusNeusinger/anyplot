# bar-pareto: Pareto Chart with Cumulative Line

## Description

A Pareto chart combining descending-sorted bars (by frequency or count) with a cumulative percentage line overlay on a secondary y-axis. This visualization helps identify the most significant factors in a dataset by applying the Pareto principle (80/20 rule), making it one of the "7 Basic Tools of Quality" in Six Sigma and quality management. It reveals which categories contribute the most to an overall effect, enabling data-driven prioritization.

## Applications

- Quality control: identifying the most frequent defect types in a manufacturing process to prioritize corrective actions
- Business operations: analyzing customer complaint categories to focus improvement efforts on the highest-impact areas
- Six Sigma: performing root cause analysis by ranking failure modes by frequency during DMAIC projects

## Data

- `category` (string) - Names of the categories being analyzed (e.g., defect types, complaint reasons)
- `count` (numeric) - Frequency or count for each category
- Size: 5-15 categories (enough to show meaningful distribution without clutter)
- Example: Manufacturing defect data with types like "Scratches", "Dents", "Cracks", "Misalignment", "Discoloration" and their occurrence counts

## Notes

- Bars must be sorted in descending order by value (largest to smallest, left to right)
- Cumulative percentage line uses a secondary y-axis (0-100%)
- Include an 80% horizontal reference line to highlight the 80/20 threshold
- Primary y-axis shows raw counts/frequency; secondary y-axis shows cumulative percentage
- Cumulative line markers should be placed at the center-top of each bar

## What a good version looks like

- A good version shows: bars sorted by count from the largest on the left to the smallest on the right, each rising from a zero baseline on a count axis that is never truncated.
- A good version shows: a cumulative percentage line with one marker per bar, centered over its bar, rising at every step to a hundred percent at the last bar, on a secondary axis running from zero to a hundred percent.
- A good version shows: the reference line the Notes ask for at the eighty percent mark of the percentage axis, visible in both themes, so the vital few categories left of where the cumulative line crosses it stand out.
- A good version shows: both y axes labeled, counts on one side and cumulative percentage on the other, so the bars read against one axis and the line against the other.
- Expected, not a defect: a few tall bars followed by a long tail of short ones, a cumulative line that flattens toward the end, and a crossing of the reference line wherever the data puts it rather than at an exact 80/20 split.
