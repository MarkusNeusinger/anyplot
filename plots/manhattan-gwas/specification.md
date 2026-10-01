# manhattan-gwas: Manhattan Plot for GWAS

## Description

A Manhattan plot visualizes genome-wide association study (GWAS) results by displaying -log10 transformed p-values across chromosomal positions. Points are arranged by genomic position along the x-axis with alternating colors for each chromosome, making it easy to identify significant associations. A horizontal threshold line indicates genome-wide significance (typically p < 5×10⁻⁸). This plot is essential for identifying genetic variants associated with traits or diseases.

## Applications

- Identifying significant SNPs in genome-wide association studies for complex diseases
- Visualizing genetic association results across the entire genome in pharmacogenomics research
- Presenting GWAS findings in scientific publications and research presentations
- Screening for candidate loci in agricultural genomics and breeding programs

## Data

- `chromosome` (categorical) - Chromosome identifier (1-22, X, Y, or MT)
- `position` (integer) - Base pair position along the chromosome
- `p_value` (float) - P-value from association test (will be -log10 transformed)
- `snp_id` (string, optional) - SNP identifier for labeling significant hits
- Size: 100,000 - 1,000,000+ variants typical for GWAS
- Example: Simulated GWAS data with random p-values and some significant peaks

## Notes

- X-axis should show cumulative genomic position with chromosome labels centered below their region
- Use alternating colors (e.g., blue/gray) for adjacent chromosomes for visual distinction
- Include horizontal dashed line at -log10(5×10⁻⁸) ≈ 7.3 for genome-wide significance threshold
- Optionally include suggestive threshold line at -log10(1×10⁻⁵) = 5
- Consider point size reduction for dense datasets to prevent overplotting
- Significant SNPs above threshold may be labeled or highlighted with different color

## What a good version looks like

- A good version shows: one point per variant at the height of its -log10 p-value, with the chromosomes laid end to end along x in order; this cumulative layout is the type's convention, and within a chromosome each point sits at its base-pair position, never jittered.
- A good version shows: each chromosome's label centered below its own region of the x axis, as the Notes ask.
- A good version shows: adjacent chromosomes in alternating colors, as the Notes ask, so chromosome boundaries read without separators, with both colors visible in both themes.
- A good version shows: a dashed horizontal line at the genome-wide significance threshold, as the Notes ask, running across all chromosomes, and the suggestive threshold line the Notes allow, if drawn, below it and distinguishable from it.
- A good version shows: the significant variants standing out above the band of unassociated ones; the reduced point size the Notes suggest for dense data, if used, keeps that band from clotting, and the labels or highlight color the Notes allow for significant variants, if used, sit at the peaks they mark.
- Expected, not a defect: heavy overplotting in the band of non-significant variants along the bottom, columns of stacked points at associated loci, chromosomes of unequal width, and most chromosomes without any variant above the threshold.
