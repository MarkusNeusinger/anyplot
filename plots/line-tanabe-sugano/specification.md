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
- `term` (categorical) — term symbol of the curve as a plain-text key, e.g. `⁴T₁g(F)`, `⁴T₂g`, `⁴A₂g`, `⁴T₁g(P)`, `²Eg`, `²T₁g`, `²T₂g`, `²A₁g`; the drawn label is typeset from it (see Notes)
- `energy_over_b` (numeric) — reduced term energy E/B relative to the ground term, typically 0–80
- `spin_allowed` (boolean, optional) — whether the term has the same spin multiplicity as the ground term; for d⁴–d⁷, where the ground term changes at the crossover, the flag refers to the high-spin ground term, so it stays one value per term
- Size: the terms within the plotted E/B range × 200–400 field-strength samples for one dⁿ configuration, keeping every root of a symmetry and multiplicity block that falls in range, so that an avoided crossing keeps both of its curves
- Example: d⁷ (Co²⁺) at C/B = 4.63, energies from the Tanabe-Sugano matrices; ⁴T₁g(F) is the ground term up to the high-spin/low-spin crossover near Δ_o/B = 21.7 and ²Eg beyond it

## Notes

- One dⁿ configuration per chart; prefer a d⁴–d⁷ configuration (d⁶ and d⁷ are classic textbook examples), because only these have the high-spin/low-spin crossover, whose vertical line and kink make the diagram recognizable, while d², d³ and d⁸ remain valid choices without a crossover; state the configuration and the C/B ratio used in the title or a subtitle, since curve shapes depend on it
- Curve energies follow from diagonalizing the Tanabe-Sugano matrices for the chosen dⁿ at a fixed C/B ratio, then subtracting the ground-term energy at each Δ_o/B — do not approximate the curves with hand-fitted splines
- The ground term is flat at E/B = 0 by construction; draw it as a visible curve along the axis, not as an omitted baseline
- Emphasize spin-allowed terms (same multiplicity as the ground term) with thicker solid lines; draw spin-forbidden terms thinner or dashed, since they correspond to weak absorptions; for d⁴–d⁷ either classify every term against the high-spin ground term across the whole chart, or switch the emphasis at the crossover to the terms sharing the low-spin ground term's multiplicity
- Label each curve with its term symbol near the right edge (or along the curve where the plot is crowded); render the label with the library's text markup so the multiplicity is a superscript and the numeral and g are subscripts, rather than printing the plain-text `term` key; a library without such markup prints the Unicode key as is and leaves the g on the baseline
- For d⁴–d⁷: draw a vertical dashed line at the high-spin/low-spin crossover, annotated with the Δ_o/B value, and note that curves change slope discontinuously there because the reference ground term switches
- Avoided crossings between terms of the same symmetry and spin multiplicity must stay as curved near-touches — do not let the lines cross or swap identity, and draw both curves of an avoided crossing that falls in the plotted range rather than only the lowest root of the block
- Optional: a vertical marker at an example complex's Δ_o/B with its observed transitions drawn as arrows from the ground term up to the excited terms
- Near-square plot area with both axes starting at 0; a light grid helps readers slide a ruler across the chart
- Differs from `energy-level-atomic`, which shows discrete atomic levels at fixed energies with transition arrows; here the term energies are continuous functions of ligand-field strength
- Reference: [Tanabe-Sugano Diagrams (Chemistry LibreTexts)](https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Supplemental_Modules_and_Websites_(Inorganic_Chemistry)/Crystal_Field_Theory/Tanabe-Sugano_Diagrams) — confirms the Δ_o/B versus E/B axis convention, the vertical crossover line for d⁴–d⁷, and that the Racah A parameter is dropped as approximately constant
- Reference: [Tanabe-Sugano Diagrams, appendix (Chemistry LibreTexts)](https://chem.libretexts.org/Bookshelves/Inorganic_Chemistry/Inorganic_Chemistry_(LibreTexts)/16%3A_Appendix/16.03%3A_Tanabe-Sugano_Diagrams) — gives the crossover positions of its d⁴–d⁷ diagrams, including Δ_o/B = 21.7 for d⁷, without stating the C/B ratio each diagram uses; the position shifts with C/B, so compute it from the energies rather than hard-coding a quoted value

## What a good version looks like

- A good version shows: one continuous curve per term for a single dⁿ configuration, E/B against Δ_o/B, smooth apart from the crossover kink, the ground term a visible flat line at E/B = 0, and terms of the same symmetry and multiplicity never crossing, only nearly touching, both curves drawn, as the Notes ask.
- A good version shows: spin-allowed terms, those with the ground term's multiplicity, as thicker solid lines and spin-forbidden terms thinner or dashed, as the Notes ask, so the two classes can be told apart in both themes; for d⁴ to d⁷ it may follow the high-spin ground term or switch at the crossover.
- A good version shows: every curve labeled with its term symbol near the right edge or along the curve, as the Notes ask, with the multiplicity as a true superscript and the numeral and g label as true subscripts where the library has text markup, and each label readable as belonging to one curve.
- A good version shows: for d⁴ to d⁷, a vertical dashed line at the high-spin/low-spin crossover annotated with its Δ_o/B value, as the Notes ask, with the curves kinking exactly at that line; an example complex's marker, if drawn, as its own vertical line with arrows from the ground term up to the excited terms.
- A good version shows: the configuration and the C/B ratio stated in the title or a subtitle, and both axes starting at 0 on a near-square plot area, as the Notes ask, with a grid, if drawn, light enough to stay behind the curves.
- Expected, not a defect: curves of different symmetry or multiplicity crossing, curves sharing both only nearly touching, near-coincident curves, labels close together where curves converge, a kink in every curve at the crossover for d⁴ to d⁷, and no crossover line outside d⁴ to d⁷; all inherent to the diagram.
