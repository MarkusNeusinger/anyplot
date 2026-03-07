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
