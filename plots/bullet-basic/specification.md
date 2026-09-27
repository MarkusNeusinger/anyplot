# bullet-basic: Basic Bullet Chart

## Description

A bullet chart displays a single measure against qualitative ranges and a target marker, designed by Stephen Few as a space-efficient alternative to gauge charts. The linear format shows actual performance as a bar, a target as a vertical marker, and background bands representing qualitative ranges (poor/satisfactory/good). Its compact design allows multiple bullet charts to fit on a single dashboard for easy comparison across metrics.

## Applications

- Displaying sales performance against quarterly quotas in executive dashboards
- Showing project completion percentage against milestone targets in PMO reports
- Comparing actual vs budgeted expenses across departments in financial reviews
- Visualizing quality metrics (defect rates, SLA compliance) against acceptable thresholds

## Data

- `actual` (numeric) - The current/measured value to display as the primary bar
- `target` (numeric) - The goal or target value shown as a vertical marker line
- `ranges` (list of numeric) - Thresholds defining qualitative bands (e.g., [50, 75, 100] for poor/satisfactory/good)
- `label` (string, optional) - Category or metric name for the bullet chart
- Size: Single value display per bullet; multiple bullets can be stacked vertically
- Example: actual = 75, target = 90, ranges = [50, 75, 100] for a KPI at 75% with 90% target

## Notes

- Use grayscale shading for background bands to keep focus on the primary measure bar
- The target marker should be a thin contrasting line (often black) perpendicular to the bar
- Horizontal orientation is most common; vertical can be used when space requires it
- Consider adding the actual value as a text label for precise reading
- Multiple bullet charts should align on a common scale when comparing related metrics

## What a good version looks like

- A good version shows: a measure bar, narrower than the bands behind it, extending from zero to the actual value on a linear scale, so its length stays proportional to the value.
- A good version shows: the target as a thin marker line perpendicular to the measure bar at the target value, contrasting with both the bar and the bands in both themes.
- A good version shows: the qualitative bands as grayscale shades in a steady light-to-dark progression behind the bar, each ending at its threshold and distinguishable from its neighbors and from the page in both themes.
- A good version shows: several bullets, if drawn, stacked with their labels beside them and aligned on one common scale where they compare related metrics.
- A good version shows: the basic variant's three layers per bullet (bands, measure bar and target marker), with the actual-value label the Notes allow, one measure-bar color throughout, and no color change by performance, trend line or extra series.
- Expected, not a defect: the target marker drawn across the measure bar, a measure that falls short of or passes the target, and bands with no color bar or legend entry, since their shading marks qualitative ranges and encodes no data.
