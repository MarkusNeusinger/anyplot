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

## What a good version looks like

- A good version shows: strain on the x axis and engineering stress in MPa on the y axis, each material's curve as one continuous line through its samples from the origin to its fracture point; several materials, if overlaid as the Notes allow, are told apart by color and named.
- A good version shows: the elastic, plastic (strain hardening) and necking regions labeled, as the Notes ask, each label placed at the part of the curve it names.
- A good version shows: the yield point, the ultimate tensile strength and the fracture point marked and labeled, as the Notes ask: yield where the offset line meets the curve, UTS at the curve's highest stress and fracture at its last point.
- A good version shows: the offset line drawn parallel to the elastic region and shifted by 0.002 strain, as the Notes ask, rising from the strain axis to the curve and distinguishable from the curve itself.
- A good version shows: the elastic modulus annotated as the slope of the elastic region, by a visible slope line or a text annotation, as the Notes ask.
- Expected, not a defect: an elastic segment so steep that it hugs the stress axis, with the offset line and the yield marker close beside it, a yield plateau or small drop after yielding, stress falling after the UTS as the specimen necks, and a curve that ends abruptly at fracture.
