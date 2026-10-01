# smith-chart-basic: Smith Chart for RF/Impedance

## Description

A Smith chart is a specialized circular diagram used in RF engineering to display complex impedance and reflection coefficients on a normalized polar grid. The chart features constant resistance circles (centered along the horizontal axis) and constant reactance arcs (curving from the right edge), enabling engineers to visualize impedance matching, transmission line behavior, and antenna characteristics. It reveals relationships between impedance, admittance, and reflection coefficient that would be difficult to interpret in Cartesian coordinates.

## Applications

- Designing impedance matching networks for RF circuits and antennas
- Analyzing transmission line impedance transformations along electrical length
- Visualizing complex S-parameters and reflection coefficients in microwave circuits
- Optimizing antenna feed point matching to minimize VSWR

## Data

- `frequency` (numeric) - Frequency points in Hz for impedance measurements
- `z_real` (numeric) - Real part of complex impedance (resistance in ohms)
- `z_imag` (numeric) - Imaginary part of complex impedance (reactance in ohms)
- `z0` (numeric, optional) - Reference impedance for normalization (default: 50 ohms)
- Size: 10-200 frequency points recommended for smooth impedance locus curves
- Example: S11 measurements from a vector network analyzer across 1-6 GHz

## Notes

- Draw standard Smith chart grid with constant resistance circles and constant reactance arcs
- Normalize impedance values to reference impedance (Z/Z0) before plotting
- Plot impedance locus as a connected curve showing frequency sweep trajectory
- Add frequency labels at key points along the impedance curve
- Optional: Include VSWR circles (constant reflection coefficient magnitude)
- Chart boundary represents |gamma| = 1 (total reflection)
- Center of chart is matched condition (Z = Z0, gamma = 0)

## What a good version looks like

- A good version shows: the standard Smith chart grid in place of Cartesian axes, as the Notes ask: constant resistance circles that all touch the right-hand end of the horizontal axis and constant reactance arcs curving away from that point, inside a boundary that appears as a true circle.
- A good version shows: the impedance locus as one connected curve through the points in frequency order, as the Notes ask, each point where its normalized impedance Z/Z0 falls on the grid, so a matched point sits at the chart center.
- A good version shows: frequency labels at key points along the locus, as the Notes ask, each tied to its point so the direction of the sweep can be read.
- A good version shows: a grid light enough to stay behind the locus yet traceable in both themes, with normalized resistance and reactance values, if printed, each sitting on its own circle or arc.
- A good version shows: the basic variant's standard impedance chart with one locus: besides the grid, the frequency labels the Notes ask for, the VSWR circles the Notes allow and a mark at the matched center, no admittance grid, further reference lines, highlighted regions, other callouts or second locus.
- Expected, not a defect: arcs crowding together toward the right-hand point where they all converge, grid lines passing behind the locus, a locus that loops or covers only a small part of the disc, and no Cartesian axes, ticks or axis titles.
