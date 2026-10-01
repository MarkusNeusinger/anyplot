# energy-level-atomic: Atomic Energy Level Diagram

## Description

An energy level diagram displays quantized energy states as horizontal lines positioned at their respective energy values, with vertical arrows representing transitions between levels. This visualization reveals the discrete nature of atomic and molecular energy structures, making it essential for understanding spectral series, electron configurations, and quantum state transitions. It provides an intuitive way to connect abstract quantum numbers to observable spectral phenomena.

## Applications

- Visualizing hydrogen atom energy levels and spectral series (Lyman, Balmer, Paschen) to understand atomic emission and absorption spectra
- Showing molecular orbital energy diagrams in chemistry to illustrate bonding, antibonding, and nonbonding interactions
- Illustrating laser transitions and stimulated emission processes for photonics and quantum optics education
- Teaching quantum mechanics concepts such as energy quantization, selection rules, and degeneracy in atomic physics courses

## Data

- `level` (string) - quantum state label identifying the energy level (e.g., n=1, n=2, 1s, 2p)
- `energy` (numeric) - energy value in eV or arbitrary units, determining vertical position of the level line
- `transitions` (list of tuples, optional) - pairs of levels connected by arrows representing emission or absorption events, each with optional wavelength/label
- Size: 5-15 energy levels, 3-10 transitions
- Example: Hydrogen atom energy levels from n=1 to n=6 with Lyman and Balmer series transitions

## Notes

- Horizontal lines should span partial width of the plot area, not full width, and be labeled with quantum numbers or orbital designations
- Downward arrows represent emission transitions; upward arrows represent absorption transitions
- Color arrows by wavelength or frequency of the transition to convey spectral information visually
- Group levels by quantum number, orbital type, or angular momentum when showing complex atoms
- Energy axis should increase upward with clear scale markings; consider using a nonlinear scale for levels that converge near the ionization limit
- Include an ionization energy reference line at the top if applicable

## What a good version looks like

- A good version shows: each level as a horizontal line at its energy value on an energy axis that increases upward with scale markings, as the Notes ask, spanning only part of the plot width and labeled with its quantum number or orbital designation.
- A good version shows: transitions as arrows whose two ends sit on the levels they connect, pointing downward for emission and upward for absorption, as the Notes ask, spread out horizontally so each arrow can be followed from level to level.
- A good version shows: arrows colored by the wavelength or frequency of their transition, as the Notes ask, on a continuous scale or by spectral region, and visible against the background in both themes.
- A good version shows: an ionization energy reference line at the top, where the system has an ionization limit, as the Notes ask, told apart from the level lines by its style or label.
- A good version shows: the energy axis to scale, or on the nonlinear scale the Notes allow for converging levels with ticks that show it, while horizontal position is schematic: line length, arrow spacing and any grouping of levels into columns are layout, not data.
- Expected, not a defect: upper levels crowding together below the ionization limit, a large empty gap above the ground state, arrows of very different lengths side by side, and a compressed or broken energy scale; all follow from the level structure.
