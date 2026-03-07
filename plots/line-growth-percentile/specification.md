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
