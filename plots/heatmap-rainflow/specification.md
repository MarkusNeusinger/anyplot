# heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis

## Description

A rainflow counting matrix visualizes the results of rainflow cycle counting from a load or stress time history. The matrix displays cycle counts as a 2D heatmap where one axis represents cycle amplitude (half-range), the other represents cycle mean value, and color intensity represents the frequency of each cycle combination. This is a fundamental tool in fatigue analysis and durability engineering, used to characterize variable-amplitude loading for fatigue life prediction.

## Applications

- Fatigue life prediction and damage assessment of mechanical components under variable-amplitude loading
- Analyzing load spectra from real-world measurements on vehicles, aircraft structures, or wind turbines
- Comparing measured vs. design load spectra in structural and mechanical engineering quality assurance
- Identifying dominant cycle combinations that contribute most to cumulative fatigue damage

## Data

- `amplitude` (numeric) — half-range of each counted cycle (stress or load units)
- `mean` (numeric) — mean value of each counted cycle (stress or load units)
- `count` (numeric) — number of cycles at each amplitude-mean combination
- Size: 10x10 to 64x64 bins typical for binned rainflow matrices
- Example: Rainflow counting results from a simulated or measured variable-amplitude load signal with ~20 amplitude bins and ~20 mean bins

## Notes

- Display as a 2D heatmap with amplitude on the y-axis and mean on the x-axis
- Use a sequential colormap (e.g., viridis or hot) with a logarithmic or linear color scale to clearly distinguish high-frequency from low-frequency cycle bins
- Include a colorbar indicating cycle count values
- Axis labels should indicate physical units (e.g., MPa, kN) where applicable
- Consider adding axis tick labels corresponding to bin centers or edges
- Zero-count bins should be visually distinct (e.g., white or transparent background)

## What a good version looks like

- A good version shows: cycle amplitude on the y axis and cycle mean on the x axis, as the Notes ask, every bin as a filled cell at its amplitude and mean, and physical units in the axis labels where the data has them.
- A good version shows: a sequential colormap for the cycle count on a logarithmic or linear scale, as the Notes allow, chosen so that frequent and rare bins can be told apart, with the color bar the Notes ask for naming the count and matching that scale.
- A good version shows: zero-count bins visually distinct from counted ones, as the Notes ask, so a bin with few cycles is never mistaken for an empty one in either theme.
- A good version shows: axis ticks, if labeled by bin, sitting at the bin centers or edges they name.
- Expected, not a defect: most of the matrix empty, counts piled into the low-amplitude bins, a few isolated high-amplitude bins with very low counts, and an occupied region that narrows toward large amplitudes.
