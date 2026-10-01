# ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display

## Description

A multi-channel electrocardiogram display showing the 12 standard ECG leads arranged in clinical format. Each lead displays realistic P-QRS-T wave complexes on a medical-standard grid background with calibration markers. This visualization replicates the familiar layout used in hospitals and clinics worldwide, making it immediately recognizable to healthcare professionals and useful for medical education.

## Applications

- Cardiology: displaying heart rhythm and electrical activity for clinical review
- Medical education: teaching ECG interpretation with labeled leads and waveform anatomy
- Clinical dashboards: patient monitoring displays in hospital information systems
- Research: cardiac signal analysis and arrhythmia classification visualization

## Data

- `time` (numeric, seconds) - time axis for each lead waveform, typically 2.5s per column at 25mm/s paper speed
- `lead_I`, `lead_II`, `lead_III` (numeric, mV) - limb leads
- `lead_aVR`, `lead_aVL`, `lead_aVF` (numeric, mV) - augmented limb leads
- `lead_V1` through `lead_V6` (numeric, mV) - precordial leads
- Size: 2500 samples per lead at 1000 Hz sampling rate (2.5 seconds per strip)
- Example: synthetically generated normal sinus rhythm with realistic P-QRS-T morphology

## Notes

- Arrange leads in standard clinical 3x4 grid layout: columns (I, aVR, V1, V4), (II, aVL, V2, V5), (III, aVF, V3, V6)
- Optionally include a full-length Lead II rhythm strip across the bottom
- Grid background should use standard ECG paper styling: light lines at 1mm intervals, bold lines at 5mm intervals, with a distinct paper-like color (light red/pink or light orange)
- Include a 1mV calibration pulse at the start or margin of the display
- Standard scale: 25mm/s horizontal (time), 10mm/mV vertical (voltage)
- Each lead must be clearly labeled with its standard name
- Signal amplitude should show typical normal ranges: P-wave ~0.1-0.25mV, QRS ~0.5-2.0mV, T-wave ~0.1-0.5mV
- Generate synthetic ECG data programmatically (e.g., using sine/cosine combinations or a simple mathematical ECG model) rather than requiring external data files

## What a good version looks like

- A good version shows: the 12 leads in the standard clinical 3x4 layout, grouped as the Notes give (I, aVR, V1, V4), (II, aVL, V2, V5), (III, aVF, V3, V6), every strip clearly labeled with its standard lead name, as the Notes ask.
- A good version shows: ECG paper behind every strip, as the Notes ask: light lines at 1mm intervals and bold lines at 5mm intervals in a paper-like light red, pink or light orange, with square grid cells and traces that stand out from the ruling in both themes.
- A good version shows: a 1mV calibration pulse at the start or in the margin, as the Notes ask, drawn as a rectangular step on the same grid, with every strip sharing the standard scale of 25mm/s and 10mm/mV so the pulse and the traces can be measured against the ruling.
- A good version shows: in every lead a baseline with repeating P-QRS-T complexes at their sampled voltages, the QRS the largest deflection and the P and T waves smaller, in the typical normal amplitude ranges the Notes give.
- A good version shows: the Lead II rhythm strip the Notes allow, if drawn, running the full width across the bottom on the same grid and scale, labeled as Lead II.
- Expected, not a defect: thin traces on a dense ruling, no numeric axes or tick labels because the grid and the calibration pulse carry the scale, only a few beats per strip, complexes that differ in size and direction between leads, such as mostly downward ones in aVR, and small P waves.
