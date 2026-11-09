""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: ochre (wood) carries the dark squares by the semantic exception
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DARK_SQUARE = IMPRINT_PALETTE[3]

# Light squares: a pale tint of the same ochre, identical in both themes
LIGHT_SQUARE = "#E8D5B8"

# Data: board parameters — files (columns) left to right, ranks (rows) bottom to top
FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANKS = [1, 2, 3, 4, 5, 6, 7, 8]

# Plot: one stacked layer per rank, one unit segment per file
title = "chessboard-basic · python · pygal · anyplot.ai"
title_font_size = round(66 * min(1.0, 67 / len(title)))

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(DARK_SQUARE,),
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=56,
    legend_font_size=44,
    value_font_size=36,
    opacity=1.0,
    opacity_hover=1.0,
    transition="0s",
)

# Histogram bars take explicit (height, start, end) spans and no gap between them,
# so each square is a bar from file index f to f + 1
board = pygal.Histogram(
    style=style,
    width=2400,
    height=2400,
    title=title,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=0,
    margin_top=120,
    margin_bottom=220,
    margin_left=210,
    margin_right=210,
    print_values=False,
    truncate_label=-1,
    xrange=(0, len(FILES)),
    range=(0, len(RANKS)),
    x_labels=[{"label": file, "value": f + 0.5} for f, file in enumerate(FILES)],
    y_labels=[{"label": str(rank), "value": r + 0.5} for r, rank in enumerate(RANKS)],
)

# Ranks are drawn top down: each lower rank's bars paint over the taller ones,
# leaving one visible square per file. Light squares sit where file index +
# rank index is odd, so h1 and a8 are light.
for r in reversed(range(len(RANKS))):
    squares = [
        {
            "value": (r + 1, f, f + 1),
            "label": f"{FILES[f]}{RANKS[r]}",
            "style": f"fill: {LIGHT_SQUARE if (f + r) % 2 else DARK_SQUARE}; stroke: {INK}; stroke-width: 2",
        }
        for f in range(len(FILES))
    ]
    board.add(str(RANKS[r]), squares)

# Save
board.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as fh:
    fh.write(board.render())
