""" anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Created: 2026-04-30
"""

import os
import sys


# Pop script directory so local pygal.py doesn't shadow the installed package
_script_dir = sys.path.pop(0)
import cairosvg  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Use pygal Style to validate palette consistency
_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=48,
    label_font_size=36,
)

# Canvas
WIDTH = 4800
HEIGHT = 2700
MARGIN_L = 400
MARGIN_R = 440
MARGIN_T = 220
MARGIN_B = 130
NODE_W = 52
NODE_GAP = 40

# Data — energy flow in TWh (sources → end-use sectors)
node_labels = [
    "Coal",
    "Natural Gas",
    "Nuclear",
    "Renewables",
    "Residential",
    "Commercial",
    "Industrial",
    "Transportation",
]
N_SRC = 4  # first 4 are sources; rest are targets

flows = [
    (0, 4, 5),  # Coal → Residential
    (0, 5, 8),  # Coal → Commercial
    (0, 6, 25),  # Coal → Industrial
    (1, 4, 22),  # Gas → Residential
    (1, 5, 18),  # Gas → Commercial
    (1, 6, 15),  # Gas → Industrial
    (1, 7, 3),  # Gas → Transportation
    (2, 4, 12),  # Nuclear → Residential
    (2, 5, 10),  # Nuclear → Commercial
    (2, 6, 8),  # Nuclear → Industrial
    (3, 4, 8),  # Renewables → Residential
    (3, 5, 6),  # Renewables → Commercial
    (3, 6, 5),  # Renewables → Industrial
    (3, 7, 4),  # Renewables → Transportation
]

# Compute per-node totals
node_total = [0] * len(node_labels)
for src, tgt, val in flows:
    node_total[src] += val
    node_total[tgt] += val

# Layout: vertical scale so the taller column fills available height
avail_h = HEIGHT - MARGIN_T - MARGIN_B
n_src_gaps = N_SRC - 1
n_tgt_gaps = len(node_labels) - N_SRC - 1
scale = (avail_h - max(n_src_gaps, n_tgt_gaps) * NODE_GAP) / sum(node_total[:N_SRC])

# Node y positions
node_x = []
node_y0 = []
node_y1 = []

# Source nodes (left column)
src_block_h = sum(node_total[i] * scale for i in range(N_SRC)) + n_src_gaps * NODE_GAP
y = MARGIN_T + (avail_h - src_block_h) / 2
for i in range(N_SRC):
    h = node_total[i] * scale
    node_x.append(MARGIN_L)
    node_y0.append(y)
    node_y1.append(y + h)
    y += h + NODE_GAP

# Target nodes (right column)
tgt_indices = list(range(N_SRC, len(node_labels)))
tgt_block_h = sum(node_total[i] * scale for i in tgt_indices) + n_tgt_gaps * NODE_GAP
y = MARGIN_T + (avail_h - tgt_block_h) / 2
for i in tgt_indices:
    h = node_total[i] * scale
    node_x.append(WIDTH - MARGIN_R - NODE_W)
    node_y0.append(y)
    node_y1.append(y + h)
    y += h + NODE_GAP

# Link paths (cubic bezier ribbons)
src_cursor = list(node_y0[:N_SRC])
tgt_cursor = list(node_y0[N_SRC:])
link_data = []
for src, tgt, val in flows:
    h = val * scale
    x1 = node_x[src] + NODE_W
    y1t = src_cursor[src]
    y1b = y1t + h
    src_cursor[src] += h

    tgt_local = tgt - N_SRC
    x2 = node_x[tgt]
    y2t = tgt_cursor[tgt_local]
    y2b = y2t + h
    tgt_cursor[tgt_local] += h

    cx = (x1 + x2) / 2
    path = (
        f"M {x1:.1f},{y1t:.1f} "
        f"C {cx:.1f},{y1t:.1f} {cx:.1f},{y2t:.1f} {x2:.1f},{y2t:.1f} "
        f"L {x2:.1f},{y2b:.1f} "
        f"C {cx:.1f},{y2b:.1f} {cx:.1f},{y1b:.1f} {x1:.1f},{y1b:.1f} Z"
    )
    c = OKABE_ITO[src]
    r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    link_data.append((f"rgba({r},{g},{b},0.40)", path))


def hex_to_rgba(hex_color, alpha=1.0):
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


# Build SVG string
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
    f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{PAGE_BG}"/>',
    # Title
    f'<text x="{WIDTH // 2}" y="{MARGIN_T // 2}" text-anchor="middle" '
    f'dominant-baseline="middle" font-family="sans-serif" font-size="48" '
    f'font-weight="600" fill="{INK}">'
    f"Energy Distribution · sankey-basic · pygal · anyplot.ai</text>",
    '<g id="links">',
]
for fill, path in link_data:
    parts.append(f'<path d="{path}" fill="{fill}" stroke="none"/>')
parts.append("</g>")

# Nodes
parts.append('<g id="nodes">')
for i in range(len(node_labels)):
    color = OKABE_ITO[i] if i < N_SRC else INK_SOFT
    x = node_x[i]
    y0 = node_y0[i]
    h = node_y1[i] - node_y0[i]
    parts.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{NODE_W}" height="{h:.1f}" fill="{color}" rx="5"/>')
parts.append("</g>")

# Labels
parts.append('<g id="labels">')
for i in range(len(node_labels)):
    y_mid = (node_y0[i] + node_y1[i]) / 2
    label = node_labels[i]
    val_str = f"{node_total[i]} TWh"
    if i < N_SRC:
        tx = node_x[i] - 24
        anchor = "end"
    else:
        tx = node_x[i] + NODE_W + 24
        anchor = "start"
    parts.append(
        f'<text x="{tx:.1f}" y="{y_mid - 22:.1f}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" font-family="sans-serif" font-size="38" '
        f'font-weight="500" fill="{INK}">{label}</text>'
    )
    parts.append(
        f'<text x="{tx:.1f}" y="{y_mid + 26:.1f}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" font-family="sans-serif" font-size="28" '
        f'fill="{INK_MUTED}">{val_str}</text>'
    )
parts.append("</g>")
parts.append("</svg>")

svg_content = "\n".join(parts)

# Save HTML (pygal-style interactive output)
html_content = (
    f'<!DOCTYPE html><html><head><meta charset="utf-8">'
    f"<title>sankey-basic · pygal · anyplot.ai</title>"
    f"<style>body{{margin:0;background:{PAGE_BG}}}</style></head>"
    f"<body>{svg_content}</body></html>"
)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fh:
    fh.write(html_content)

# Save PNG via cairosvg (same pipeline pygal.render_to_png uses internally)
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=f"plot-{THEME}.png")
