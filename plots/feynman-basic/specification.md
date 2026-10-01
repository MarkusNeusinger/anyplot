# feynman-basic: Feynman Diagram for Particle Interactions

## Description

A Feynman diagram visualizes interactions between subatomic particles in quantum field theory. Different line styles represent different particle types: straight lines for fermions (electrons, quarks), wavy lines for photons, curly/looped lines for gluons, and dashed lines for scalar bosons (e.g., Higgs). Lines meet at vertices representing interaction points. Invented by Richard Feynman, these diagrams are both a computational tool and a cultural icon of modern physics.

## Applications

- Illustrating electron-positron annihilation producing a photon in a particle physics lecture
- Visualizing quantum electrodynamics (QED) processes such as Compton scattering or pair production
- Documenting Feynman rules and vertex factors in a quantum field theory textbook or reference

## Data

- `particles` (list of dict) - Each particle with fields: `id` (string), `type` (string: fermion|photon|gluon|boson), `label` (string, e.g., "e-", "gamma", "g")
- `vertices` (list of dict) - Interaction points with `id` (string) and `position` (tuple of x, y)
- `propagators` (list of dict) - Connections between vertices: `from_vertex` (string), `to_vertex` (string), `particle_id` (string)
- Size: Typically 2-6 vertices, 3-10 propagators
- Example: Electron-positron annihilation — two fermion lines entering a vertex, one photon line exiting to a second vertex, two fermion lines leaving

## Notes

- Use distinct line styles: solid/straight for fermions (with arrow for particle direction), wavy for photons, curly/looped for gluons, dashed for scalar bosons
- Arrows on fermion lines indicate particle vs antiparticle flow (convention: particle flows forward in time, antiparticle backward)
- Time axis typically runs left to right; label it if helpful
- Place vertex dots or small circles at interaction points
- Label each propagator with the particle symbol (e-, e+, gamma, g, H, etc.)
- Keep the layout clean and symmetric where possible; Feynman diagrams prioritize clarity over data density

## What a good version looks like

- A good version shows: each propagator in the line style of its particle type, as the Notes ask: fermions as solid straight lines with an arrow, photons as wavy lines, gluons as curly, looped lines and scalar bosons as dashed lines, the styles distinguishable by shape alone.
- A good version shows: arrows on fermion lines that follow the convention the Notes give, forward in time for particles and backward for antiparticles, so the arrow direction runs unbroken through every vertex.
- A good version shows: a dot or small circle at every interaction point, as the Notes ask, with the lines meeting exactly at it, and every propagator labeled with its particle symbol next to its own line.
- A good version shows: time running in one direction across the diagram, typically left to right as the Notes say, labeled if helpful, with positions schematic: vertices are laid out, not plotted, symmetric where possible, and only which lines meet at which vertex carries meaning.
- A good version shows: the basic variant's standard diagram: besides the line styles, arrows, vertex dots and particle labels the Notes ask for, the time-direction label the Notes allow and a key to the line styles, no reference lines, highlighted lines or regions, callouts, formulas or data plots alongside.
- Expected, not a defect: no data axes, ticks or grid, positions and line lengths that carry no scale, lines of very different lengths, a diagram that uses only some of the line styles because its process has only those particles, and empty space around the diagram.
