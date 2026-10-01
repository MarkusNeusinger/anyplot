# sequence-logo-basic: Sequence Logo for Motif Visualization

## Description

A sequence logo visualizes the consensus of multiple aligned DNA, RNA, or protein sequences. At each position, letters are stacked vertically with height proportional to information content (measured in bits), and individual letter heights within the stack reflect their relative frequency. This is the standard visualization for identifying conserved positions in transcription factor binding sites, splice sites, and protein domains.

## Applications

- Visualizing transcription factor binding site motifs from ChIP-seq or SELEX experiments
- Analyzing conserved regions in multiple protein sequence alignments to identify functional domains
- Displaying splice site consensus sequences in gene annotation studies
- Characterizing enzyme active site conservation across species

## Data

- `position` (integer) — position along the aligned sequence (1 to N)
- `letter` (string) — nucleotide (A, C, G, T) for DNA or amino acid single-letter code for protein
- `frequency` (float) — relative frequency of each letter at the given position, values between 0 and 1, summing to 1 per position
- Size: 5–30 positions, 4 letters for DNA/RNA or 20 letters for protein sequences
- Example: a 10-position DNA motif representing a transcription factor binding site, with frequency distributions at each position

## Notes

- Stack letters vertically at each position, ordered by frequency (most frequent on top)
- Scale the total stack height by information content in bits (max 2 bits for DNA, max ~4.32 bits for protein)
- Use standard color schemes: DNA — A=green, C=blue, G=orange/yellow, T=red; protein — chemistry-based coloring (e.g., hydrophobic, polar, charged groups)
- X-axis shows position numbers; Y-axis shows information content in bits
- Letters should be rendered as scaled glyphs (stretched to fill their allocated height), not as plain text
- Include axis labels: "Position" for x-axis, "Information content (bits)" for y-axis

## What a good version looks like

- A good version shows: one stack of letters per position, placed by construction and not by a data coordinate per letter: the stack's total height is the position's information content in bits, read on a y axis from zero, and each letter's share of the stack is its relative frequency.
- A good version shows: the letters in every stack ordered by frequency at that position, with the most frequent on top, as the Notes ask.
- A good version shows: the letters as scaled glyphs stretched to fill their allocated height, as the Notes ask, so that a letter's drawn height is its value, not plain text at one font size placed on a colored bar.
- A good version shows: the standard color scheme the Notes give (for DNA, A green, C blue, G orange or yellow, T red; for protein, chemistry-based groups), each letter keeping its color at every position and all of them readable in both themes.
- A good version shows: the basic variant's logo alone: besides the stacked letters, the position numbers on the x axis and the information axis in bits, no reference or mean lines, highlight bands or boxes on conserved positions, callouts, error bars, consensus text row or companion panel.
- Expected, not a defect: very short stacks at poorly conserved positions, with letters too small to read or a nearly empty column, stack heights that differ strongly along the motif, stacks well below the maximum of the axis, and letterforms distorted by the stretching.
