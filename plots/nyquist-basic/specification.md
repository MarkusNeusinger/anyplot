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

## What a good version looks like

- A good version shows: the open-loop response as one continuous curve through its real and imaginary parts in frequency order, on axes labeled Real and Imaginary with a 1:1 aspect ratio, as the Notes ask.
- A good version shows: the critical point (-1, 0) marked with a distinct marker, as the Notes ask, at its true position, told apart from the curve and the frequency markers in both themes, inside a plot window that shows how the curve passes it.
- A good version shows: a unit circle centered at the origin, as the Notes ask, that appears circular, stays subordinate to the response curve and is visible in both themes.
- A good version shows: arrows on the curve pointing toward increasing frequency, and frequency values annotated at selected key points such as the gain and phase crossovers, as the Notes ask, each label at the point it names.
- A good version shows: the basic variant's Nyquist plot of one system: besides the critical point, unit circle, arrows and frequency labels the Notes ask for, axes through the origin and a fainter mirrored branch for negative frequencies, no further reference lines, highlighted regions, other callouts or second system.
- Expected, not a defect: a curve that passes close to the critical point, bunches toward the origin at high frequency, leaves the plot window at low frequency when the gain grows without bound, and fills only part of the plane, with the unit circle small beside a high-gain curve.
