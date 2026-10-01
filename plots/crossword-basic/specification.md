# crossword-basic: Crossword Puzzle Grid

## Description

A crossword puzzle grid visualization with white entry cells for letters, black blocking cells, and numbered starting positions for across and down words. The symmetric black cell pattern follows traditional newspaper-style crossword conventions, creating a clean and recognizable puzzle layout suitable for printing or digital display.

## Applications

- Printable crossword puzzles for newspapers and puzzle books
- Educational vocabulary exercises and language learning tools
- Custom puzzle generation for events or themed activities
- Interactive puzzle games and mobile applications

## Data

- `grid` (2D array) - Binary pattern indicating blocked (1) and entry (0) cells
- `numbers` (dict) - Mapping of cell positions to clue numbers for word starts
- Size: 10x10 to 15x15 cells typical for standard crosswords
- Example: 15x15 grid with symmetric black cell pattern and numbered word positions

## Notes

- White cells for letter entry, black cells for blocking
- Numbers placed in top-left corner of cells that start words (across or down)
- Traditional 180-degree rotational symmetry for black cell placement
- Clean, uniform grid lines separating all cells
- Monochrome design optimized for printing
- Cell aspect ratio should be 1:1 (square cells)

## What a good version looks like

- A good version shows: square cells on a fixed grid, separated by uniform grid lines, as the Notes ask, with entry cells white and blocking cells a solid black that stays darker than the entry cells in both themes.
- A good version shows: a small number in the top-left corner of every cell that starts an across or a down word, as the Notes ask, and in no other cell, rising in reading order from left to right and top to bottom, readable in both themes and leaving room for a letter.
- A good version shows: a black cell pattern with 180-degree rotational symmetry, as the Notes ask, so that the grid turned upside down shows the same pattern.
- A good version shows: entry cells that form one connected area, which the black cells do not cut into separate parts, the newspaper convention the Description points to.
- A good version shows: the basic variant's empty grid in the monochrome design the Notes ask for: besides the cells, the grid lines and the clue numbers, no filled-in answers, clue list, tinted or highlighted cells or entries, reference lines or callouts.
- Expected, not a defect: no data axes, ticks or legend, empty entry cells without letters, numbers that are small next to their cells, and black cells in uneven clusters with large open white areas.
