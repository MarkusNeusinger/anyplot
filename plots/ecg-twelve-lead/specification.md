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
