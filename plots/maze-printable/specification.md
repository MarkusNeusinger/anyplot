# maze-printable: Printable Maze Puzzle

## Description

A rectangular maze puzzle visualization with clearly marked start and goal positions. The maze is algorithmically generated to guarantee exactly one solution path from start to finish. The clean black-and-white design is optimized for printing, allowing users to solve the puzzle with a pen or pencil.

## Applications

- Printable activity sheets for children's entertainment and education
- Puzzle books and newspapers requiring programmatically generated mazes
- Educational materials teaching algorithmic thinking and problem-solving
- Restaurant placemats and waiting room entertainment

## Data

- `width` (int) - Number of cells horizontally (recommended: 15-40)
- `height` (int) - Number of cells vertically (recommended: 15-40)
- `seed` (int, optional) - Random seed for reproducible maze generation
- Size: Grid dimensions determine complexity (larger = harder)
- Example: 25x25 grid with start at top-left, goal at bottom-right

## Notes

- Use maze generation algorithms (DFS, Prim's, Kruskal's) that guarantee a single solution
- Start position typically marked with "S" or arrow, goal with "G" or star
- Interior wall thickness should be consistent and print-friendly (not too thin); the outer boundary may be drawn heavier
- Include adequate margins for printing
- Walls in strong contrast with the passages in both themes; black on white in the light theme for maximum contrast and ink efficiency
- Passage width should accommodate pen/pencil marking

## What a good version looks like

- A good version shows: a rectangular grid of equal cells whose walls run straight along the cell edges, horizontally and vertically, inside an outer boundary that is closed apart from an entrance and an exit opening, if the maze has them; position is construction here, with no data axes.
- A good version shows: the start and the goal each clearly marked, with a letter, an arrow, a star or a similar mark as the Notes suggest, readable in both themes and told apart at a glance.
- A good version shows: a maze that can be solved from start to goal along exactly one route, as the Notes ask, with no wall sealing off either end and no second way through.
- A good version shows: interior walls of one consistent thickness that are not hairline thin, with the outer boundary optionally heavier, as the Notes ask, in strong contrast with the passages in both themes and black on white in the light theme, and passages wide enough to mark with a pen or pencil.
- A good version shows: a margin of empty space around the whole maze, as the Notes ask, so that no wall or marker touches the edge of the image.
- Expected, not a defect: no data axes, ticks, grid or legend, many dead ends, a texture of long winding corridors or of many short branches depending on the generation algorithm, and no solution path drawn.
