# heatmap-loss-triangle: Actuarial Loss Development Triangle

## Description

A triangular matrix visualization showing cumulative insurance claim payments developing over time. Rows represent accident/origin years, columns represent development periods (e.g., 1-10 years), with the upper-left triangle displaying actual observed cumulative claims and the lower-right triangle showing projected/estimated values (IBNR). This plot is essential for actuarial reserving, enabling analysts to visualize the chain-ladder method and identify development patterns in loss data.

## Applications

- Insurance reserving: visualizing cumulative claims development to estimate IBNR (Incurred But Not Reported) reserves using the chain-ladder method
- Reinsurance pricing: assessing reserve adequacy and treaty pricing by examining historical loss development patterns
- Financial reporting: preparing loss reserve disclosures and communicating reserve estimates to stakeholders

## Data

- `accident_year` (integer) - The origin/accident year when claims occurred (e.g., 2015-2024)
- `development_period` (integer) - The development period in years from origin (e.g., 1-10)
- `cumulative_amount` (float) - Cumulative claim payments at each development stage
- `is_projected` (boolean) - Whether the value is actual (observed) or projected (estimated)
- `development_factor` (float) - Age-to-age development factors between consecutive periods
- Size: 10 accident years x 10 development periods (triangular: ~55 actual + ~45 projected cells)
- Example: Cumulative paid claims triangle with accident years 2015-2024 and development periods 1-10

## Notes

- The upper-left triangle contains actual/observed values; the lower-right triangle contains projected values
- Use distinct visual styling (e.g., different background colors or hatching) to clearly differentiate actual from projected cells
- The diagonal from top-right to bottom-left represents the latest evaluation date
- Annotate each cell with the cumulative amount value (formatted with thousands separator)
- Display age-to-age development factors between column headers or as a separate row below the triangle
- Color intensity should encode the magnitude of cumulative amounts
- Include a clear legend distinguishing actual vs projected regions
- Row labels show accident/origin years; column headers show development periods
