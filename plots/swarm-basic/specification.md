# swarm-basic: Basic Swarm Plot

## Description

A swarm plot (beeswarm plot) displays individual data points for categorical comparisons, with points spread horizontally to avoid overlap. This reveals the full distribution shape and density while preserving exact values - combining the benefits of strip plots (individual points) and violin plots (density visualization). Ideal when you need to see every observation rather than just summary statistics.

## Applications

- Comparing response times across different experimental conditions in psychology research
- Visualizing patient biomarker levels across treatment groups in clinical trials
- Analyzing employee performance scores by department
- Displaying student test scores by classroom to identify patterns and outliers

## Data

- `category` (categorical) - Group labels for comparison on the categorical axis
- `value` (numeric) - Continuous variable values shown on the value axis
- Size: 20-300 observations total (swarm plots become cluttered with too many points)
- Example: Performance metrics across 3-5 groups with 30-60 observations per group

## Notes

- Points should be sized appropriately to show spread without excessive overlap
- Use consistent point sizes within the plot
- Consider adding a subtle mean or median marker for each category
- Color can distinguish categories or encode an additional variable
- Maintain clear spacing between category groups

## What a good version looks like

- A good version shows: every observation as its own point at its value on the value axis, pushed sideways only as far as needed to sit beside its neighbors instead of on them, so each swarm is widest where values are densest.
- A good version shows: points of one size throughout, as the Notes ask, sized so each swarm shows its spread without points hiding one another.
- A good version shows: clear space between the swarms of neighboring categories, as the Notes ask, even where the swarms are widest.
- A good version shows: the basic variant's swarms only, with color that distinguishes the categories or encodes an additional variable and the subtle per-category mean or median marker the Notes allow, and no box or violin behind the points, other reference lines, highlighted points or bands, or callouts.
- Expected, not a defect: sideways offsets, which are layout rather than data, swarms of different width with lumpy or lopsided outlines, points packed edge to edge in the densest value range, and isolated outliers.
