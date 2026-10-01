# maze-circular: Circular Maze Puzzle

## Description

A circular maze puzzle visualization featuring concentric rings connected by radial passages. Unlike rectangular mazes, this design creates a unique solving experience where the player navigates inward through ring-shaped corridors. The maze has an entry point on the outer edge and a goal at the center, with algorithmically generated walls ensuring exactly one solvable path.

## Applications

- Printable puzzle sheets with a distinctive circular aesthetic
- Decorative maze art for posters, coasters, or wall prints
- Game level design for maze-based video games or apps
- Educational activities teaching spatial reasoning and problem-solving

## Data

- `rings` (int) - Number of concentric rings (recommended: 5-10)
- `difficulty` (string) - Difficulty level affecting passage density: "easy", "medium", or "hard"
- `seed` (int, optional) - Random seed for reproducible maze generation
- Size: More rings and higher difficulty increase complexity
- Example: 7 rings with medium difficulty, entry at outer edge, goal at center

## Notes

- Concentric circular walls form ring-shaped corridors
- Radial walls divide each ring into sectors
- Radial passages connect adjacent rings at strategic points
- Entry point clearly marked on the outer perimeter
- Goal/finish clearly marked at the center
- Maze generation algorithm must guarantee exactly one solution
- Black walls on white background for print-friendly output
- Wall thickness should be consistent and suitable for pen/pencil solving

## What a good version looks like

- A good version shows: concentric circular walls around one common center forming ring-shaped corridors, radial walls dividing each ring into sectors, and openings that connect neighboring rings, as the Notes describe; position is construction here, with no data axes.
- A good version shows: the entry clearly marked at an opening on the outer perimeter and the goal clearly marked at the center, as the Notes ask, with the markers readable in both themes and not blocking a corridor.
- A good version shows: a maze that can be solved from the entry to the center along exactly one route, as the Notes require, with no wall sealing off the entry or the goal and no second way through.
- A good version shows: walls of one consistent thickness, as the Notes ask, drawn as solid lines in strong contrast with the corridors in both themes, and corridors wide enough to trace with a pen or pencil.
- Expected, not a defect: no data axes, ticks, grid or legend, many dead ends, long curved corridors, more sectors in the outer rings than near the center, and no solution path drawn; the maze is a puzzle to solve, not a chart to read.
