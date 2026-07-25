"""anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: pygal 3.1.3 | Python 3.13.12
Quality: pending | Updated: 2026-07-25
"""

import os
import sys


# Pop script dir so this file (pygal.py) doesn't shadow the installed pygal package
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

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# pygal Style is the single source of truth for all Imprint tokens.
# pygal has no native Sankey chart class, so the diagram itself is built as raw
# SVG below (also true of every other pygal Sankey in this codebase) — but every
# color/font value the SVG uses is read back off this Style object rather than
# hardcoded twice.
chart_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=66,
    label_font_size=56,
    value_font_size=36,
    font_family="sans-serif",
)

# Read all visual tokens from the Style object — single source of truth
BG = chart_style.background
FG = chart_style.foreground
FG_SUBTLE = chart_style.foreground_subtle
PALETTE = chart_style.colors
LABEL_SIZE = chart_style.label_font_size
VALUE_SIZE = chart_style.value_font_size
FONT = chart_style.font_family

# Canvas — 3200x1800 landscape (Step 0 hard contract)
WIDTH = 3200
HEIGHT = 1800
MARGIN_L = 620
MARGIN_R = 400
MARGIN_T = 170
MARGIN_B = 100
NODE_W = 36
NODE_GAP = 26
BREATHING_ROOM = 0.90  # shrink node/link scale so columns don't touch top/bottom margins

# Dominant flows get higher opacity to direct attention to key pathways
ALPHA_DOMINANT = 0.72
ALPHA_DEFAULT = 0.48
DOMINANT_THRESHOLD = 20  # MLD (million liters per day)

# Data — municipal water distribution, sources to end-use sectors (MLD)
node_labels = [
    "Mountain Reservoir",
    "Groundwater Wells",
    "River Intake",
    "Desalination Plant",
    "Residential",
    "Agriculture",
    "Industrial",
    "Municipal",
]
N_SRC = 4  # first 4 are sources; rest are targets

flows = [
    (0, 4, 28),  # Mountain Reservoir -> Residential  <- dominant
    (0, 5, 12),  # Mountain Reservoir -> Agriculture
    (0, 7, 6),  # Mountain Reservoir -> Municipal
    (1, 4, 18),  # Groundwater Wells -> Residential
    (1, 5, 32),  # Groundwater Wells -> Agriculture   <- dominant
    (1, 6, 9),  # Groundwater Wells -> Industrial
    (1, 7, 3),  # Groundwater Wells -> Municipal
    (2, 4, 10),  # River Intake -> Residential
    (2, 5, 15),  # River Intake -> Agriculture
    (2, 6, 22),  # River Intake -> Industrial         <- dominant
    (2, 7, 5),  # River Intake -> Municipal
    (3, 4, 14),  # Desalination Plant -> Residential
    (3, 5, 2),  # Desalination Plant -> Agriculture
    (3, 6, 8),  # Desalination Plant -> Industrial
    (3, 7, 4),  # Desalination Plant -> Municipal
]

# Compute per-node totals
node_total = [0] * len(node_labels)
for src, tgt, val in flows:
    node_total[src] += val
    node_total[tgt] += val

# Layout: vertical scale so the taller column fills available height, with
# breathing room left top/bottom (previous review: whitespace too tight)
avail_h = HEIGHT - MARGIN_T - MARGIN_B
n_src_gaps = N_SRC - 1
n_tgt_gaps = len(node_labels) - N_SRC - 1
scale = (avail_h - max(n_src_gaps, n_tgt_gaps) * NODE_GAP) / sum(node_total[:N_SRC]) * BREATHING_ROOM

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
    c = PALETTE[src]  # color drawn from Style object palette
    r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    alpha = ALPHA_DOMINANT if val >= DOMINANT_THRESHOLD else ALPHA_DEFAULT
    dominant = val >= DOMINANT_THRESHOLD
    # Ribbon midpoint for annotation placement
    ribbon_mid_y = (y1t + y1b + y2t + y2b) / 4
    tooltip = f"{node_labels[src]} → {node_labels[tgt]}: {val} MLD"
    link_data.append((f"rgba({r},{g},{b},{alpha})", path, dominant, cx, ribbon_mid_y, val, tooltip))

# Title — scale fontsize down for long titles (see plot-generator.md "Title
# fontsize must scale with title length")
title_text = "Water Distribution Network · sankey-basic · python · pygal · anyplot.ai"
title_ratio = 67 / len(title_text) if len(title_text) > 67 else 1.0
title_size = max(44, round(chart_style.title_font_size * title_ratio))

# Build SVG string. pygal ships no Sankey chart class, so nodes/links are drawn
# as raw SVG (colors/fonts still sourced from chart_style above). Hover
# highlighting + native <title> tooltips give the HTML output real
# interactivity even without pygal's own chart JS.
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
    "<style>.flow{transition:opacity 0.15s ease}.flow:hover{opacity:0.95 !important}.node:hover{opacity:0.85}</style>",
    f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>',
    # Title — font size from chart_style.title_font_size, scaled for length
    f'<text x="{WIDTH // 2}" y="{MARGIN_T // 2}" text-anchor="middle" '
    f'dominant-baseline="middle" font-family="{FONT}" font-size="{title_size}" '
    f'font-weight="700" fill="{FG}">{title_text}</text>',
    '<g id="links">',
]

# Non-dominant flows drawn first (background layer)
for fill, path, dominant, _cx, _ribbon_mid_y, _val, tooltip in link_data:
    if not dominant:
        parts.append(f'<path class="flow" d="{path}" fill="{fill}" stroke="none"><title>{tooltip}</title></path>')

# Dominant flows drawn on top with annotation showing their magnitude
for fill, path, dominant, cx, ribbon_mid_y, val, tooltip in link_data:
    if dominant:
        parts.append(f'<path class="flow" d="{path}" fill="{fill}" stroke="none"><title>{tooltip}</title></path>')
        parts.append(
            f'<text x="{cx:.1f}" y="{ribbon_mid_y:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-family="{FONT}" font-size="{VALUE_SIZE}" '
            f'font-weight="700" fill="{FG}" opacity="0.80">{val} MLD</text>'
        )

parts.append("</g>")

# Nodes
parts.append('<g id="nodes">')
for i in range(len(node_labels)):
    color = PALETTE[i] if i < N_SRC else INK_SOFT
    x = node_x[i]
    y0 = node_y0[i]
    h = node_y1[i] - node_y0[i]
    parts.append(
        f'<rect class="node" x="{x:.1f}" y="{y0:.1f}" width="{NODE_W}" height="{h:.1f}" '
        f'fill="{color}" rx="5"><title>{node_labels[i]}: {node_total[i]} MLD</title></rect>'
    )
parts.append("</g>")

# Labels — font sizes from chart_style.label_font_size / chart_style.value_font_size
parts.append('<g id="labels">')
for i in range(len(node_labels)):
    y_mid = (node_y0[i] + node_y1[i]) / 2
    label = node_labels[i]
    val_str = f"{node_total[i]} MLD"
    if i < N_SRC:
        tx = node_x[i] - 24
        anchor = "end"
    else:
        tx = node_x[i] + NODE_W + 24
        anchor = "start"
    parts.append(
        f'<text x="{tx:.1f}" y="{y_mid - 30:.1f}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" font-family="{FONT}" font-size="{LABEL_SIZE}" '
        f'font-weight="500" fill="{FG}">{label}</text>'
    )
    parts.append(
        f'<text x="{tx:.1f}" y="{y_mid + 34:.1f}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" font-family="{FONT}" font-size="{VALUE_SIZE}" '
        f'fill="{FG_SUBTLE}">{val_str}</text>'
    )
parts.append("</g>")
parts.append("</svg>")

svg_content = "\n".join(parts)

# Save HTML (pygal-style interactive output — hover a flow or node for its tooltip)
html_content = (
    f'<!DOCTYPE html><html><head><meta charset="utf-8">'
    f"<title>sankey-basic · pygal · anyplot.ai</title>"
    f"<style>body{{margin:0;background:{BG}}}</style></head>"
    f"<body>{svg_content}</body></html>"
)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fh:
    fh.write(html_content)

# Save PNG via cairosvg (same pipeline pygal.render_to_png uses internally)
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=f"plot-{THEME}.png")
