# bifurcation-basic: Bifurcation Diagram for Dynamical Systems

## Description

A bifurcation diagram shows how the steady-state behavior of a dynamical system changes as a control parameter varies. By plotting the long-term values of a state variable against a continuously varied parameter, it reveals transitions from stable fixed points through period-doubling cascades to chaotic regimes. The classic example is the logistic map, where the route to chaos is clearly visible as the growth rate parameter increases.

## Applications

- Studying the onset of chaos through period-doubling cascades in nonlinear dynamical systems
- Analyzing population dynamics and carrying capacity transitions in ecology
- Understanding period-doubling routes and mode-locking in laser physics
- Teaching nonlinear dynamics and chaos theory with the logistic map as a canonical example

## Data

- `parameter` (numeric) — Bifurcation parameter (e.g., r in the logistic map), typically ranging from 2.5 to 4.0
- `state` (numeric) — Steady-state or periodic orbit values of the iterated variable after transients are discarded
- Size: 100,000+ points (many state values per parameter value, sampled after discarding transient iterations)
- Example: Logistic map x(n+1) = r * x(n) * (1 - x(n)), iterating for each r value and recording the last N states

## Notes

- Use very small point size (1px or smaller) with low alpha transparency to create density-based visualization
- Show the full period-doubling cascade from period-1 through period-2, period-4, etc., leading into chaos
- Use the logistic map x(n+1) = r * x(n) * (1 - x(n)) as the default example system
- Label key bifurcation points where period-doubling occurs (e.g., r ~ 3.0, 3.449, 3.544)
- For each parameter value, discard initial transient iterations (e.g., first 200) and plot the subsequent values (e.g., next 100)
- Parameter axis should span at least 2.5 to 4.0 to capture the full route from stability to chaos
