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
