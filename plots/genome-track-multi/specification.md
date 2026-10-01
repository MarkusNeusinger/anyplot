# genome-track-multi: Genome Track Viewer

## Description

A multi-track genome browser view that displays different types of genomic data aligned along a shared chromosomal coordinate axis. Multiple parallel horizontal tracks (gene annotations, read coverage, variants, regulatory elements) are stacked vertically, each showing a different data type at the same genomic locus. This visualization is essential for integrative genomics, enabling researchers to explore relationships between gene structure, expression, variation, and regulation in a single coordinated view.

## Applications

- Exploring gene structure and regulatory regions at specific genomic loci
- Visualizing sequencing read coverage alongside gene annotations to assess expression levels
- Displaying variant calls (SNPs, indels) in their genomic context relative to exons and regulatory elements
- Integrating multi-omics data (epigenomics, transcriptomics, variants) at a single locus for biological interpretation

## Data

- `chromosome` (string) - Chromosome identifier (e.g., "chr1", "chrX")
- `start` (integer) - Start position of the genomic feature in base pairs
- `end` (integer) - End position of the genomic feature in base pairs
- `track` (categorical) - Data track the feature belongs to (e.g., "genes", "coverage", "variants", "regulatory")
- `feature_type` (categorical, optional) - Sub-type within a track (e.g., "exon", "intron", "UTR" for gene track; "SNP", "indel" for variant track)
- `value` (numeric, optional) - Quantitative value such as coverage depth, variant quality score, or regulatory activity score
- `strand` (categorical, optional) - Strand direction ("+" or "-") for gene annotations
- `label` (string, optional) - Feature name or identifier (e.g., gene name, variant ID)
- Size: 10-100 features across 3-5 tracks spanning a single genomic region

## Notes

- Stack 3-5 tracks vertically with a shared x-axis representing genomic position (base pair coordinates)
- Gene track: use rectangles for exons, thin lines for introns, and arrows or chevrons to indicate strand direction
- Coverage track: render as a filled area plot showing read depth across the region
- Variant track: display as tick marks or lollipop markers at variant positions, with optional height encoding quality or effect size
- Regulatory track (optional): show as colored rectangles indicating enhancers, promoters, or other regulatory elements
- Each track should have a clear label on the left side identifying the data type
- Use consistent genomic coordinates across all tracks with position labels on the x-axis
- Consider using subtle background shading to visually separate adjacent tracks

## What a good version looks like

- A good version shows: the tracks stacked vertically over one shared genomic position axis with position labels, each track labeled on its left with its data type, as the Notes ask, and every feature drawn from its start to its end coordinate, so features line up across tracks.
- A good version shows: the gene track with each gene drawn from its start to its end, its exons as rectangles joined by thin intron lines where the data distinguishes them, as the Notes ask, and, where the data gives a strand, arrows or chevrons that show each gene's strand direction.
- A good version shows: the coverage track as a filled area of read depth across the region, as the Notes ask, rising from the track's own zero baseline.
- A good version shows: the variant track as tick marks or lollipop markers at the variant positions, as the Notes ask; marker height, if it encodes quality or effect size as the Notes allow, is measured from the track's baseline.
- A good version shows: the regulatory track, if included, as colored rectangles spanning each element, with the colors telling enhancers, promoters and other element types apart and named in a legend or by labels.
- Expected, not a defect: tracks of different height, long empty stretches between features, uneven coverage peaks, a separate value scale for each quantitative track, and overlapping genes on separate rows inside the gene track, where the row is layout and only the coordinates are data.
