# line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory

## Description

A Tanabe-Sugano diagram plots the energies of the electronic term states of a transition-metal ion in an octahedral ligand field as continuous functions of the field strength. The x-axis is the reduced ligand-field strength Δ_o/B (octahedral splitting divided by the Racah parameter B) and the y-axis is the reduced term energy E/B measured from the ground term, which therefore runs along the x-axis itself as a horizontal line at E/B = 0. Each term — labeled with its full symbol including spin multiplicity and Mulliken label — is one curve, and for d⁴–d⁷ a vertical line marks the high-spin/low-spin crossover where the ground term changes and every curve kinks. Chemists read the chart in reverse: matching ratios of observed UV-Vis band energies against the curves yields both Δ_o and B for a real complex.

## Applications

- Assigning d-d absorption bands in the UV-Vis spectrum of a coordination complex to specific term-to-term transitions
- Estimating the octahedral splitting Δ_o and the Racah parameter B of a complex from two or three measured band positions
- Teaching crystal field and ligand field theory, where the diagram connects term symbols to observable spectra
- Predicting whether a given dⁿ ion with a given ligand set is high-spin or low-spin from the position of its Δ_o/B relative to the crossover

## Data

- `delta_over_b` (numeric) — reduced ligand-field strength Δ_o/B, sampled across 0–40 (dense enough that avoided crossings stay smooth, typically 200–400 points)
- `term` (categorical) — term symbol of the curve, e.g. `⁴A₂g`, `⁴T₂g`, `⁴T₁g(F)`, `²Eg`, `²T₁g`, `⁴T₁g(P)`
- `energy_over_b` (numeric) — reduced term energy E/B relative to the ground term, typically 0–80
- `spin_allowed` (boolean, optional) — whether the term has the same spin multiplicity as the ground term
- Size: 6–12 term curves × 200–400 field-strength samples for one dⁿ configuration
- Example: d³ (Cr³⁺) at C/B = 4.5, energies from the Tanabe-Sugano matrices with ⁴A₂g as the ground term

## Notes

- One dⁿ configuration per chart (d³ and d⁶ are the classic textbook examples); state the configuration and the C/B ratio used in the title or a subtitle, since curve shapes depend on it
- Curve energies follow from diagonalizing the Tanabe-Sugano matrices for the chosen dⁿ at a fixed C/B ratio, then subtracting the ground-term energy at each Δ_o/B — do not approximate the curves with hand-fitted splines
- The ground term is flat at E/B = 0 by construction; draw it as a visible curve along the axis, not as an omitted baseline
- Emphasize spin-allowed terms (same multiplicity as the ground term) with thicker solid lines; draw spin-forbidden terms thinner or dashed, since they correspond to weak absorptions
- Label each curve with its term symbol near the right edge (or along the curve where the plot is crowded); superscript multiplicities and subscript g labels must render correctly
- For d⁴–d⁷: draw a vertical dashed line at the high-spin/low-spin crossover, annotated with the Δ_o/B value, and note that curves change slope discontinuously there because the reference ground term switches
- Avoided crossings between terms of the same symmetry must stay as curved near-touches — do not let the lines cross or swap identity
- Optional: a vertical marker at an example complex's Δ_o/B with its observed transitions drawn as arrows from the ground term up to the excited terms
- Equal-aspect or near-square plot area with both axes starting at 0; a light grid helps readers slide a ruler across the chart
- Differs from `energy-level-atomic`, which shows discrete atomic levels at fixed energies with transition arrows; here the term energies are continuous functions of ligand-field strength
- Reference: [Tanabe-Sugano Diagrams (Chemistry LibreTexts)](https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Supplemental_Modules_and_Websites_(Inorganic_Chemistry)/Crystal_Field_Theory/Tanabe-Sugano_Diagrams) — confirms the Δ_o/B versus E/B axis convention, the vertical crossover line for d⁴–d⁷, and that the Racah A parameter is dropped as approximately constant

## What a good version looks like

- A good version shows: one continuous curve per term for a single dⁿ configuration, E/B against Δ_o/B, smooth apart from the crossover kink, with the ground term drawn as a visible flat line at E/B = 0 along the x-axis, as the Notes ask, and the configuration and C/B ratio stated in the title or a subtitle.
- A good version shows: spin-allowed terms, those with the ground term's multiplicity, as thicker solid lines and spin-forbidden terms thinner or dashed, as the Notes ask, so the two classes can be told apart in both themes; for d⁴ to d⁷ it may follow the high-spin ground term or switch at the crossover.
- A good version shows: every curve labeled with its term symbol near the right edge or along the curve, as the Notes ask, with the multiplicity as a true superscript and the numeral and g label as true subscripts, and each label readable as belonging to one curve.
- A good version shows: for d⁴ to d⁷, a vertical dashed line at the high-spin/low-spin crossover annotated with its Δ_o/B value, as the Notes ask, with the curves kinking exactly at that line.
- A good version shows: both axes starting at 0 on an equal-aspect or near-square plot area, as the Notes ask; a grid, if drawn, light enough to stay behind the curves; and an example complex's marker, if drawn, as a vertical line at its Δ_o/B with arrows rising from the ground term to the excited terms it reaches.
- Expected, not a defect: curves of different symmetry or multiplicity crossing, curves sharing both only nearly touching, near-coincident curves, labels close together where curves converge, a kink in every curve at the crossover for d⁴ to d⁷, and no crossover line outside d⁴ to d⁷; all inherent to the diagram.
