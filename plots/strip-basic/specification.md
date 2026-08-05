# strip-basic: Basic Strip Plot

## Description

A strip plot displays individual data points for each category along a single axis, with random horizontal jitter applied to reduce overplotting. Unlike box plots or violin plots that show summary statistics, strip plots reveal every observation, making them ideal for small to medium datasets where individual values matter. The random jitter spreads points horizontally within each category to show density through point accumulation.

## Applications

- Comparing distributions of test scores across different classrooms or teaching methods
- Visualizing patient response times to treatments across different drug groups
- Exploring salary distributions by department in organizational analysis
- Quality control inspection of measurements across production batches

## Data

- `category` (categorical) - Group labels for the x-axis (e.g., treatment groups, departments)
- `value` (numeric) - Numeric measurement for the y-axis
- Size: 10-200 observations per category works best
- Example: Survey response scores grouped by demographic category

## Notes

- Use moderate jitter width (0.1-0.3) to spread points without overlapping adjacent categories
- Apply transparency (alpha 0.5-0.7) when points overlap frequently
- Consider adding horizontal lines for group means or medians as reference
- For very large datasets (>200 per category), consider swarm plots or violin plots instead
