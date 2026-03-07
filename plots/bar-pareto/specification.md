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
