# nyquist-basic: Nyquist Plot for Control Systems

## Description

A Nyquist plot maps a system's open-loop frequency response onto the complex plane by plotting the imaginary part against the real part of the transfer function as frequency varies from zero to infinity. It is the primary tool for applying the Nyquist stability criterion to determine whether a closed-loop control system is stable. The plot visually reveals gain and phase margins and is widely used in classical control theory and electronic circuit design.

## Applications

- Assessing closed-loop stability of a feedback control system using the Nyquist stability criterion
- Determining gain margin and phase margin from the proximity of the curve to the critical point (-1, 0)
- Designing and tuning robust controllers for industrial processes
- Characterizing amplifier stability and loop gain in analog electronics

## Data

- `real` (numeric) — real part of the open-loop frequency response G(jw)
- `imaginary` (numeric) — imaginary part of the open-loop frequency response G(jw)
- `frequency` (numeric) — angular frequency values (rad/s) corresponding to each point
- Size: 200-1000 points, logarithmically spaced in frequency

## Notes

- Mark the critical point (-1, 0) with a distinct marker (e.g., red "x" or filled circle)
- Draw a unit circle centered at the origin for reference
- Annotate selected frequency values along the curve at key points (e.g., gain crossover, phase crossover)
- Include arrows on the curve showing the direction of increasing frequency
- Use a 1:1 aspect ratio so the unit circle appears circular
- Label axes as "Real" and "Imaginary"
