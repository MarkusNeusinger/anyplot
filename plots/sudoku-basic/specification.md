# sudoku-basic: Basic Sudoku Grid

## Description

A standard 9×9 Sudoku grid with proper visual hierarchy showing 3×3 box regions. Thick lines separate the nine boxes while thin lines divide individual cells. The clean black-and-white design is optimized for printing and solving puzzles.

## Applications

- Printable puzzle sheets for personal use or distribution
- Educational materials for teaching logic and problem-solving skills
- Game development mockups and prototyping interfaces

## Data

- `grid` (2D array, 9×9) - Integer values 0-9 where 0 represents empty cells
- Size: Fixed 9×9 grid (81 cells)
- Example: Partially filled Sudoku puzzle with starting numbers

## Notes

- Bold/thick lines for 3×3 box boundaries (every 3rd line)
- Thin lines for individual cell boundaries
- Numbers centered in cells with clear, readable font
- Empty cells shown as blank (no zero displayed)
- Monochrome design suitable for printing

## What a good version looks like

- A good version shows: a 9×9 grid of equal cells with thin lines between the cells and clearly thicker lines on the 3×3 box boundaries, as the Notes ask, the two weights distinguishable in both themes.
- A good version shows: the given numbers centered in their cells, as the Notes ask, readable in both themes and clear of the grid lines.
- A good version shows: every empty cell left blank, as the Notes ask, rather than holding a zero, a dot or another placeholder.
- A good version shows: givens that form a valid puzzle state, with no digit repeated within a row, a column or a 3×3 box.
- A good version shows: the basic variant's unsolved puzzle, monochrome as the Notes ask: besides the given numbers, the thin cell lines, the thick box borders and at most a faint alternating tint of the boxes, no solution digits or pencil marks, highlighted cells, rows, columns or boxes, reference lines or callouts.
- Expected, not a defect: no data axes, ticks or legend, most cells empty, the givens spread unevenly over the grid, and no solution shown; the grid is a puzzle to fill in, not a chart to read.
