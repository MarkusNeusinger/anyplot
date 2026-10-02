# phase-diagram: Phase Diagram (State Space Plot)

## Description

A phase diagram (or state space plot) displays the trajectory of a dynamical system by plotting a variable against its derivative (x vs dx/dt). This visualization reveals the qualitative behavior of systems including fixed points, limit cycles, stability, and oscillation patterns. It is essential for analyzing differential equations without solving them explicitly.

## Applications

- Analyzing simple harmonic oscillators and damped pendulum motion in physics education
- Studying predator-prey dynamics (Lotka-Volterra equations) in ecology
- Examining stability of electrical circuits with inductors and capacitors
- Visualizing attractors and bifurcations in nonlinear dynamics research

## Data

- `x` (numeric array) - Position or state variable values along the trajectory
- `dx_dt` (numeric array) - Derivative (velocity) values corresponding to each x
- `t` (numeric array, optional) - Time values for computing derivatives from raw position data
- Size: 200-2000 points for smooth trajectories
- Example: A simple pendulum with initial displacement, showing spiral convergence to equilibrium

## Notes

- Multiple trajectories from different initial conditions can reveal basin of attraction structure
- Fixed points (equilibria) are the states on the dx/dt = 0 axis where the system stays at rest; a trajectory that merely crosses that axis is at a turning point, not at a fixed point
- Closed loops indicate periodic oscillation (limit cycles or centers)
- Consider adding direction arrows or color gradient to show time evolution
- For damped systems, trajectories spiral inward; for driven systems, they may form limit cycles

## What a good version looks like

- A good version shows: the state variable x on the horizontal axis and its derivative dx/dt on the vertical, each trajectory as one smooth continuous curve through its points in time order.
- A good version shows: the motion's character readable from the shape, as the Notes describe: an inward spiral that ends at the equilibrium for a damped system, a loop that closes on itself for periodic oscillation.
- A good version shows: direction arrows or a color gradient, if used as the Notes suggest, running with time, which for this pair of axes means rightward above the dx/dt = 0 axis and leftward below it; a gradient is explained by a color bar or label.
- A good version shows: several trajectories from different initial conditions, if drawn as the Notes allow, each traceable from its starting point and told apart by color or start markers.
- A good version shows: fixed points, if marked, on the dx/dt = 0 axis at the equilibrium the trajectories approach or circle, with a marker that remains visible where the trajectories converge.
- Expected, not a defect: a spiral whose turns wind too tightly near the fixed point to separate, trajectories overlapping there, a closed orbit retraced many times that reads as one loop, trajectories of a driven system crossing themselves, and ellipses stretched by axes in different units.
