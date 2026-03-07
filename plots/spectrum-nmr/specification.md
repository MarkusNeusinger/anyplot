# spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)

## Description

An NMR spectrum plots signal intensity versus chemical shift (in ppm) to reveal the electronic environment of atomic nuclei in a molecule. It is the primary analytical tool in organic chemistry for determining molecular structure, with peak positions indicating functional groups and splitting patterns (multiplets) revealing connectivity between neighboring atoms. The x-axis is conventionally reversed (high ppm on the left) and peaks appear as sharp signals rising from a baseline.

## Applications

- Identifying functional groups and confirming molecular structure in organic chemistry research and pharmaceutical development
- Monitoring chemical reactions by tracking the appearance and disappearance of characteristic peaks over time
- Quality control in manufacturing to verify compound identity and purity by comparing against reference spectra

## Data

- `chemical_shift` (numeric) - chemical shift values in parts per million (ppm), typically 0-12 ppm for 1H NMR
- `intensity` (numeric) - signal intensity (arbitrary units), representing peak heights from the NMR measurement
- Size: 1000-8000 data points along the chemical shift axis
- Example: synthetic 1H NMR spectrum of ethanol showing a triplet near 1.2 ppm (CH3), a quartet near 3.7 ppm (CH2), and a singlet near 2.6 ppm (OH)

## Notes

- The x-axis must be reversed so that higher ppm values appear on the left (standard NMR convention)
- Peaks should be sharp and well-resolved with realistic splitting patterns (singlet, doublet, triplet, quartet)
- Label key peaks with their chemical shift values
- Include a reference peak at 0 ppm (TMS internal standard)
- Use a clean baseline with minimal noise to emphasize peak clarity
