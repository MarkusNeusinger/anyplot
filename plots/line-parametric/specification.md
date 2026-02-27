# line-parametric: Parametric Curve Plot

## Description

A parametric curve plot visualizes x(t) and y(t) as functions of a parameter t, tracing smooth curves in 2D space. Unlike standard function plots where y = f(x), parametric curves can loop, self-intersect, and form closed shapes such as Lissajous figures, spirals, and cardioids. This makes them essential for representing trajectories, oscillations, and classical mathematical curves that cannot be expressed as single-valued functions.

## Applications

- Visualizing Lissajous figures in physics and signal analysis to study frequency ratios and phase relationships
- Plotting spiral curves (Archimedean, logarithmic) for antenna design and natural growth patterns
- Drawing classical mathematical curves such as cardioids, cycloids, and epicycloids for education and research
- Tracing orbital paths and projectile trajectories in physics and engineering simulations

## Data

- `t` (numeric) — parameter values sampled over a defined range (e.g., 0 to 2pi)
- `x` (numeric) — x-coordinate values computed as x(t)
- `y` (numeric) — y-coordinate values computed as y(t)
- Size: 200-2000 points for smooth curves
- Example: Lissajous figure with x = sin(3t), y = sin(2t) for t in [0, 2pi]

## Notes

- Use equal aspect ratio to prevent geometric distortion of the curves
- Show direction of increasing t using a color gradient along the curve (e.g., from cool to warm colors)
- Include at least two example curves: a Lissajous figure (x = sin(3t), y = sin(2t)) and a spiral (x = t*cos(t), y = t*sin(t))
- Label start and end points or mark the direction of traversal
- Use sufficient point density to ensure smooth rendering, especially near cusps or self-intersections
