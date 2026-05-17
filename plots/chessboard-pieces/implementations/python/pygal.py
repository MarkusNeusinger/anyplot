"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
LIGHT_SQUARE = "#E8D5C4" if THEME == "light" else "#4A4136"
DARK_SQUARE = "#B5956F" if THEME == "light" else "#2D2622"

# Chess pieces Unicode mapping
PIECE_UNICODE = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}

# Example position (starting position)
pieces = {
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "Q",
    "e1": "K",
    "f1": "B",
    "g1": "N",
    "h1": "R",
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "e2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "e8": "k",
    "f8": "b",
    "g8": "n",
    "h8": "r",
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "e7": "p",
    "f7": "p",
    "g7": "p",
    "h7": "p",
}


# Create SVG chess board
def create_chessboard_svg(pieces, theme):
    """Generate SVG chessboard with pieces."""
    board_size = 800
    square_size = board_size / 8
    margin = 60
    total_width = board_size + 2 * margin
    total_height = board_size + 2 * margin + 80

    page_bg = PAGE_BG
    light_sq = LIGHT_SQUARE
    dark_sq = DARK_SQUARE
    text_color = INK
    label_color = INK_MUTED

    svg = f"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}">
  <defs>
    <style>
      .piece-text {{ font-size: {square_size * 0.6}px; text-anchor: middle; dominant-baseline: central; }}
      .label-text {{ font-size: 16px; text-anchor: middle; dominant-baseline: central; fill: {label_color}; }}
      .title-text {{ font-size: 28px; font-weight: 500; text-anchor: middle; fill: {text_color}; }}
    </style>
  </defs>
  <rect width="{total_width}" height="{total_height}" fill="{page_bg}"/>

  <!-- Title -->
  <text x="{total_width / 2}" y="35" class="title-text">chessboard-pieces · pygal · anyplot.ai</text>

  <!-- Board background -->
  <rect x="{margin}" y="{margin + 60}" width="{board_size}" height="{board_size}" fill="{dark_sq}"/>

  <!-- Board squares and pieces -->
"""

    # Draw board squares and pieces
    for rank in range(8):  # 8 to 1 (top to bottom)
        for file in range(8):  # a to h (left to right)
            x = margin + file * square_size
            y = margin + 60 + (7 - rank) * square_size

            # Determine square color (light at h1, so (h,1) = (7,0) is light)
            is_light = (file + rank) % 2 == 1

            square_color = light_sq if is_light else dark_sq
            svg += f'  <rect x="{x}" y="{y}" width="{square_size}" height="{square_size}" fill="{square_color}"/>\n'

            # Add piece if present
            file_letter = chr(ord("a") + file)
            rank_number = rank + 1
            square_name = f"{file_letter}{rank_number}"

            if square_name in pieces:
                piece = pieces[square_name]
                unicode_piece = PIECE_UNICODE[piece]
                piece_color = text_color
                piece_x = x + square_size / 2
                piece_y = y + square_size / 2
                svg += f'  <text x="{piece_x}" y="{piece_y}" class="piece-text" fill="{piece_color}">{unicode_piece}</text>\n'

    # Add file labels (a-h)
    for file in range(8):
        x = margin + file * square_size + square_size / 2
        y = margin + 60 + board_size + 25
        file_letter = chr(ord("a") + file)
        svg += f'  <text x="{x}" y="{y}" class="label-text">{file_letter}</text>\n'

    # Add rank labels (1-8)
    for rank in range(8):
        x = margin - 20
        y = margin + 60 + (7 - rank) * square_size + square_size / 2
        rank_number = rank + 1
        svg += f'  <text x="{x}" y="{y}" class="label-text">{rank_number}</text>\n'

    svg += "\n</svg>"

    return svg


# Generate and save SVG
svg_content = create_chessboard_svg(pieces, THEME)

# Save SVG
with open(f"plot-{THEME}.svg", "w") as f:
    f.write(svg_content)

# Convert SVG to PNG using cairosvg
try:
    import cairosvg

    cairosvg.svg2png(bytestring=svg_content.encode(), write_to=f"plot-{THEME}.png")
except ImportError:
    print("cairosvg not available, PNG export skipped")

# Save as HTML (SVG embedded)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>chessboard-pieces - pygal</title>
    <style>
        body {{ margin: 0; padding: 20px; background-color: {PAGE_BG}; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{svg_content}
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
