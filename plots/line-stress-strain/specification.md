# line-stress-strain: Engineering Stress-Strain Curve

## Description

An engineering stress-strain curve visualizes the relationship between applied stress (MPa) and resulting strain (dimensionless) in a material under uniaxial tensile loading. The curve reveals distinct mechanical behavior regions — elastic deformation, yielding, strain hardening, and necking — culminating in fracture. It is the foundational plot for characterizing material mechanical properties and comparing material performance.

## Applications

- Comparing mechanical properties (yield strength, UTS, ductility) of different materials or alloys for design selection
- Determining yield strength using the 0.2% offset method for structural engineering design calculations
- Quality control testing in manufacturing to verify materials meet specified mechanical property requirements
- Teaching material science and mechanics of materials concepts in engineering education

## Data

- `strain` (numeric) — engineering strain (dimensionless), typically ranging from 0 to 0.5
- `stress_mpa` (numeric) — engineering stress in megapascals (MPa)
- Size: 100-500 data points sampled from a tensile test
- Example: Tensile test data for mild steel showing elastic region, yield plateau, strain hardening, and necking to fracture

## Notes

- Label key regions on the curve: elastic, plastic (strain hardening), and necking
- Mark critical points: yield point (0.2% offset method), ultimate tensile strength (UTS), and fracture point
- Annotate the elastic modulus (Young's modulus) as the slope in the elastic region, with a visible slope line or text annotation
- Draw the 0.2% offset line (parallel to the elastic region, offset by 0.002 strain) to illustrate yield point determination
- Optional: overlay curves for multiple materials to enable direct comparison of mechanical behavior
