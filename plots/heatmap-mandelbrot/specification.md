# heatmap-mandelbrot: Mandelbrot Set Fractal Visualization

## Description

A visualization of the Mandelbrot set, the most iconic fractal in mathematics. Each pixel represents a complex number c on the complex plane, colored by how quickly the iteration z(n+1) = z(n)^2 + c diverges. The boundary between convergent and divergent regions reveals infinitely complex, self-similar structure including the characteristic cardioid and period-2 bulb.

## Applications

- Teaching complex dynamics and iteration behavior in mathematics courses
- Demonstrating self-similarity and fractal geometry concepts
- Exploring chaos theory and dynamical systems boundaries
- Creating mathematical art and educational reference materials

## Data

- `x_min`, `x_max` (numeric) — real axis range of the complex plane (default: -2.5 to 1.0)
- `y_min`, `y_max` (numeric) — imaginary axis range of the complex plane (default: -1.25 to 1.25)
- `max_iterations` (integer) — escape iteration limit controlling detail level (default: 100)
- Grid resolution: 800x600 pixels or higher

## Notes

- Color pixels by escape iteration count using a smooth, perceptually uniform colormap
- Use smooth coloring via normalized iteration count to avoid discrete color banding
- Show the full Mandelbrot set including the characteristic cardioid and period-2 bulb
- Label axes with real and imaginary coordinate values
- Points inside the set (that never escape) should be colored black or a distinct solid color
- The aspect ratio should preserve the mathematical proportions of the complex plane
