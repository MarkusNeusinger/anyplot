# chessboard-pieces: Chess Board with Pieces for Position Diagrams

## Description

A chess board visualization with pieces that can be positioned programmatically to display specific game positions, puzzles, or notable games. Pieces are defined using a dictionary mapping squares (e.g., 'e4': 'K') to standard chess notation where uppercase letters represent white pieces (K/Q/R/B/N/P) and lowercase represent black pieces (k/q/r/b/n/p). Unicode chess symbols provide clean, recognizable piece rendering.

## Applications

- Chess puzzle diagrams for tactics training and educational materials
- Game position documentation showing critical moments from famous matches
- Opening repertoire visualization for chess study and preparation
- Tournament analysis and annotated game publications

## Data

- `pieces` (dict) - Dictionary mapping square names to piece codes (e.g., {'e1': 'K', 'e8': 'k', 'd4': 'Q'})
- `square` (string) - Algebraic notation with column (a-h) and row (1-8)
- `piece` (string) - Single character: K/Q/R/B/N/P for white, k/q/r/b/n/p for black
- Example: Starting position, Scholar's Mate, or any custom arrangement

## Notes

- Use Unicode chess symbols: White pieces (U+2654 to U+2659), Black pieces (U+265A to U+265F)
- Board orientation follows standard convention with white at bottom (rows 1-2)
- Light square at h1 corner as per chess standards
- Piece symbols should be centered within their squares
- Consider slight size adjustment so pieces don't touch square edges
- Color scheme should provide good contrast for both board squares and piece visibility

## What a good version looks like

- A good version shows: a board of alternating light and dark squares in the standard orientation the Notes ask for, with white's side at the bottom and a light square at the h1 corner, bottom right.
- A good version shows: every piece on the square the position names and no piece anywhere else, centered within its square, as the Notes ask; position is the square's place on the fixed grid, not a data axis.
- A good version shows: the standard chess piece symbols, as the Notes ask, with each piece type recognizable and white pieces told apart from black pieces on light and on dark squares alike, in both themes.
- A good version shows: pieces large enough to identify and contained within their squares; the slight inset from the square edges the Notes suggest keeps neighboring pieces apart.
- A good version shows: column letters a-h and row numbers 1-8, if drawn, outside or at the rim of the board, with a at the left and row 1 at the bottom, matching the orientation.
- Expected, not a defect: no data axes, ticks, grid or legend, many empty squares, pieces crowded on one part of the board, and piece shapes that vary with the font that supplies the symbols.
