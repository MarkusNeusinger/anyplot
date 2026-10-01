# line-reaction-coordinate: Reaction Coordinate Energy Diagram

## Description

A reaction coordinate diagram plots potential energy against reaction progress, showing the energy landscape of a chemical transformation. The smooth curve traces the path from reactants through the transition state (energy maximum) to products, clearly depicting the activation energy barrier and overall enthalpy change. This fundamental chemistry visualization is essential for understanding reaction kinetics and thermodynamics.

## Applications

- Teaching activation energy and transition state theory in general chemistry courses
- Comparing catalyzed vs uncatalyzed reaction pathways to illustrate how catalysts lower activation energy
- Illustrating exothermic vs endothermic reactions by showing the relative energy levels of reactants and products
- Visualizing multi-step reaction mechanisms with intermediate species and multiple energy barriers

## Data

- `reaction_coordinate` (numeric) — Progress along the reaction path (arbitrary units, 0 to 1 or similar)
- `energy` (numeric) — Potential energy values in kJ/mol
- Size: 100-500 points for a smooth curve
- Example: A single-step exothermic reaction with reactants at 50 kJ/mol, transition state at 120 kJ/mol, and products at 20 kJ/mol

## Notes

- Label reactants, products, and transition state directly on the plot
- Show activation energy (Ea) with a double-headed arrow from reactant level to transition state peak
- Show enthalpy change (ΔH) with a double-headed arrow between reactant and product energy levels
- Use a smooth curve with a clear maximum at the transition state
- Horizontal dashed lines at reactant and product energy levels improve readability
- Use a clean, minimal style appropriate for scientific and educational contexts

## What a good version looks like

- A good version shows: one smooth, continuous curve of potential energy against reaction progress, as the Notes ask, running from the reactant level over a clear maximum at each transition state, with any intermediate as a well between two maxima, to the product level.
- A good version shows: reactants, products and the transition state labeled directly on the plot, as the Notes ask, each label next to the part of the curve it names.
- A good version shows: the activation energy Ea as a double-headed arrow from the reactant level to the transition state peak and the enthalpy change ΔH as a double-headed arrow between the reactant and product levels, as the Notes ask, each labeled, with its ends on exactly those levels.
- A good version shows: horizontal dashed lines at the reactant and product energy levels, if drawn as the Notes suggest, lighter than the curve and reaching the arrows they serve.
- A good version shows: an energy axis that is to scale, with the reactant level, the peak and the product level at their energy values, while horizontal position along the reaction coordinate is schematic, laid out for clarity and not measured.
- Expected, not a defect: a reaction coordinate axis without numeric ticks or units, a peak placed off-center, a freely chosen curve shape between the levels, and a product level above the reactant level for an endothermic reaction; only the energies are data.
