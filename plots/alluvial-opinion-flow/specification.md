# alluvial-opinion-flow: Opinion Flow Diagram

## Description

An alluvial/Sankey-style diagram showing how opinions or group memberships shift between survey waves or time periods. Flows connect the same response categories across columns, revealing patterns of opinion change, stability, and polarization. Unlike a basic alluvial diagram, this variant emphasizes distinguishing stable respondents from net changers and displays respondent totals per category at each wave.

## Applications

- Tracking voter preference changes between election polls across multiple survey waves
- Monitoring brand perception shifts over marketing campaigns using repeated consumer surveys
- Analyzing patient treatment response transitions in longitudinal clinical studies
- Studying opinion polarization in longitudinal survey data across demographic groups

## Data

- `wave` (categorical) — survey wave or time period (e.g., Wave 1, Wave 2, Wave 3)
- `source_category` (categorical) — opinion or group membership in the source wave
- `target_category` (categorical) — opinion or group membership in the target wave
- `flow_count` (numeric) — number of respondents transitioning between categories
- Size: 3-5 waves with 3-7 opinion categories each, producing 20-80 flow connections
- Example: Political opinion survey tracking 1000 respondents across 4 quarterly waves with categories like "Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"

## Notes

- Use consistent colors for each opinion category across all waves
- Flow width should be proportional to the number of respondents transitioning
- Show total respondent count per category at each wave as node labels
- Visually distinguish stable respondents (same category across waves) from changers using opacity or color intensity
- Highlight net flows between categories to reveal polarization trends
- Arrange waves left-to-right in chronological order with clear column headers
- Consider using transparency for overlapping flows to improve readability
