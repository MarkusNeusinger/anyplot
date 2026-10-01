# chessboard-basic: Chess Board Grid Visualization

## Description

A classic 8x8 chess board with alternating light and dark squares, labeled with standard algebraic notation (columns a-h, rows 1-8). This clean grid visualization serves as a foundation for chess diagrams, game position displays, and educational chess materials.

## Applications

- Chess game analysis and position diagrams for players and coaches
- Educational materials for learning chess notation and board orientation
- Game documentation and move visualization in chess publications
- Interactive chess applications and puzzle displays

## Data

- `rows` (integer) - Fixed at 8 rows (labeled 1-8)
- `columns` (integer) - Fixed at 8 columns (labeled a-h)
- Size: 64 squares (8x8 grid)
- Example: Standard chess board with white square at h1

## Notes

- Light squares traditionally appear at h1 and a8 corners
- Column labels (a-h) appear at bottom, row labels (1-8) appear on left side
- Color scheme should use classic light/dark contrast (e.g., cream/brown or white/gray)
- Square borders optional but can enhance clarity
- Board should maintain 1:1 aspect ratio for proper square proportions

## What a good version looks like

- A good version shows: an 8x8 board of equal squares alternating light and dark along every row and column, drawn at a 1:1 aspect ratio, as the Notes ask, so that every square is a true square.
- A good version shows: the standard orientation: light squares at the h1 corner, bottom right, and the a8 corner, top left, as the Notes ask.
- A good version shows: column labels a-h along the bottom and row labels 1-8 on the left side, as the Notes ask, running from a at the left to h at the right and from 1 at the bottom to 8 at the top, each centered on its column or row.
- A good version shows: a classic two-tone scheme, as the Notes ask, in which light and dark squares differ clearly from each other and the board stands out from the page in both themes.
- A good version shows: the basic variant's empty board: besides the squares, the column and row labels and the square borders the Notes allow, no pieces, move arrows, highlighted squares, reference lines or callouts.
- Expected, not a defect: an empty board with no pieces, no data axes, ticks, grid or legend, and a fully regular pattern; the board is a fixed grid by definition, not a plot of data.
