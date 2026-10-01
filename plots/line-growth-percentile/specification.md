# line-growth-percentile: Pediatric Growth Chart with Percentile Curves

## Description

A WHO/CDC-style growth chart displaying smooth percentile curves (3rd, 10th, 25th, 50th, 75th, 90th, 97th) as colored bands, with individual patient data points overlaid and connected by a line. This chart is a standard clinical tool for monitoring child development metrics such as height, weight, or BMI across age. It enables quick visual assessment of whether a child's growth trajectory falls within expected population ranges.

## Applications

- Pediatrics: tracking an individual child's growth trajectory against population reference percentiles during well-child visits
- Public health: comparing population-level growth distributions to WHO/CDC reference standards for nutritional surveillance
- Nutrition research: identifying trends in childhood malnutrition or obesity by visualizing cohort data against percentile bands
- Medical education: teaching students how to interpret growth charts and assess developmental milestones

## Data

- `age_months` (numeric) - child's age in months (x-axis), typically ranging from 0 to 240 (0-20 years)
- `measurement` (numeric) - the growth metric value (height in cm, weight in kg, or BMI in kg/m2) on the y-axis
- `percentile_3` through `percentile_97` (numeric) - reference percentile values at each age point for the 3rd, 10th, 25th, 50th, 75th, 90th, and 97th percentiles
- `patient_age` (numeric) - individual patient measurement ages
- `patient_value` (numeric) - individual patient measurement values
- Size: percentile reference curves with ~50-100 age points; 5-20 individual patient measurements
- Example: WHO weight-for-age reference data for boys aged 0-36 months with an individual patient's weight measurements at well-child visits

## Notes

- Percentile bands should be rendered as filled areas between adjacent percentile curves with graduated color intensity (darker near extremes, lighter near median)
- The 50th percentile (median) line should be visually emphasized (thicker or distinct color)
- Gender-specific coloring convention: use blue tones for boys and pink/rose tones for girls (generate the chart for one gender)
- Percentile labels (P3, P10, P25, P50, P75, P90, P97) should appear on the right margin of the chart
- Individual patient data should be plotted as connected markers overlaid on the percentile bands with a contrasting color
- X-axis should show age with appropriate units (months or years depending on range)
- Use synthetic but realistic reference data that approximates WHO/CDC growth standards

## What a good version looks like

- A good version shows: the percentile curves from the 3rd to the 97th as smooth lines at their reference values over age, stacked in order and never crossing one another.
- A good version shows: filled bands between adjacent percentile curves with graduated intensity, darker near the extremes and lighter near the median, as the Notes ask, in blue tones for boys or pink/rose tones for girls, the steps between bands distinguishable in both themes.
- A good version shows: the 50th percentile line visually emphasized, thicker or in a distinct color, as the Notes ask, so the median reads first among the reference curves.
- A good version shows: the percentile labels P3 to P97 on the right margin, as the Notes ask, each beside the end of its own curve and readable as belonging to that curve.
- A good version shows: the patient's measurements as connected markers at their ages and values, overlaid on the bands in a contrasting color, as the Notes ask, on an age axis in months or years as fits the range.
- Expected, not a defect: curves that lie close together at the youngest ages and fan out with age, bands of unequal width, steep early growth that flattens, irregularly spaced patient visits, and a patient line that crosses percentile curves or runs outside the outermost ones.
