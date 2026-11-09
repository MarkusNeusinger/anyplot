""" anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import cairosvg
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one hue per category of the first dimension, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Canvas
WIDTH, HEIGHT = 3200, 1800

# Columns: set these to your table's column names
DIMENSIONS = ["Category", "Distribution", "Payment", "Outcome"]  # role: dimension_
ORDERS = "Orders"  # role: count

# Data: replace this block with your own table, for example df = pd.read_csv("orders.csv")
paths = [
    # Electronics - balanced across channels
    ("Electronics", "Direct", "Credit Card", "Completed", 450),
    ("Electronics", "Direct", "Credit Card", "Returned", 85),
    ("Electronics", "Wholesale", "Debit Card", "Completed", 180),
    ("Electronics", "Direct", "Digital Wallet", "Completed", 280),
    ("Electronics", "Direct", "Digital Wallet", "Returned", 45),
    ("Electronics", "Wholesale", "Credit Card", "Completed", 320),
    ("Electronics", "Retail", "Digital Wallet", "Completed", 220),
    ("Electronics", "Retail", "Digital Wallet", "Cancelled", 75),
    ("Electronics", "Direct", "Credit Card", "Cancelled", 40),
    # Clothing - higher retail presence
    ("Clothing", "Direct", "Credit Card", "Completed", 320),
    ("Clothing", "Direct", "Credit Card", "Returned", 95),
    ("Clothing", "Direct", "Debit Card", "Completed", 150),
    ("Clothing", "Direct", "Debit Card", "Returned", 50),
    ("Clothing", "Retail", "Credit Card", "Completed", 480),
    ("Clothing", "Retail", "Debit Card", "Completed", 290),
    ("Clothing", "Retail", "Debit Card", "Returned", 45),
    ("Clothing", "Wholesale", "Digital Wallet", "Completed", 200),
    ("Clothing", "Wholesale", "Credit Card", "Completed", 155),
    ("Clothing", "Direct", "Digital Wallet", "Cancelled", 35),
    # Home & Garden - more wholesale/retail
    ("Home & Garden", "Retail", "Credit Card", "Completed", 420),
    ("Home & Garden", "Retail", "Debit Card", "Completed", 320),
    ("Home & Garden", "Retail", "Debit Card", "Returned", 60),
    ("Home & Garden", "Direct", "Credit Card", "Completed", 190),
    ("Home & Garden", "Direct", "Credit Card", "Returned", 35),
    ("Home & Garden", "Direct", "Digital Wallet", "Completed", 120),
    ("Home & Garden", "Wholesale", "Digital Wallet", "Completed", 110),
    # Sports - strong direct/retail mix
    ("Sports", "Direct", "Digital Wallet", "Completed", 280),
    ("Sports", "Direct", "Credit Card", "Completed", 200),
    ("Sports", "Retail", "Credit Card", "Completed", 310),
    ("Sports", "Retail", "Debit Card", "Completed", 195),
    ("Sports", "Wholesale", "Credit Card", "Completed", 240),
    ("Sports", "Wholesale", "Debit Card", "Completed", 180),
    ("Sports", "Wholesale", "Debit Card", "Returned", 35),
]
df = pd.DataFrame(paths, columns=[*DIMENSIONS, ORDERS])

# Plot: pygal draws the themed canvas and title; the axes, segments and ribbons are SVG over it
title = "parallel-categories-basic · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=round(66 * min(1.0, 67 / len(title))),
)
chart = pygal.XY(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title=title,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    dots_size=0,
    stroke=False,
    range=(0, 100),
    xrange=(0, 100),
)
chart.add("", [(50, 50)])  # an empty chart would print "No data"
base_svg = chart.render().decode("utf-8")

# Layout in SVG pixels
margin_left, margin_right, margin_top, margin_bottom = 470, 360, 300, 230
chart_width = WIDTH - margin_left - margin_right
chart_height = HEIGHT - margin_top - margin_bottom
n_dims = len(DIMENSIONS)
x_positions = [margin_left + i * chart_width / (n_dims - 1) for i in range(n_dims)]
bar_width = 80
gap_ratio = 0.05
label_size, label_pad = 44, 20
ribbon_opacity = 0.45 if THEME == "light" else 0.62
font = 'font-family="DejaVu Sans, sans-serif"'

# Category order is the data's first-appearance order; totals per category per dimension
levels = [df[dim].dropna().unique().tolist() for dim in DIMENSIONS]
# Labels right of axes 2..n get a clear lane: outgoing ribbons start past the longest label
label_lanes = [max(len(str(cat)) for cat in cats) * 0.6 * label_size + 2 * label_pad for cats in levels]
dim_totals = [df.groupby(dim, sort=False)[ORDERS].sum() for dim in DIMENSIONS]
# Past the eighth category the hues run out: the rest share the muted "other" anchor
first_colors = {cat: IMPRINT_PALETTE[i] if i < len(IMPRINT_PALETTE) else INK_MUTED for i, cat in enumerate(levels[0])}

# Segment positions: each category's length is its share of the dimension's total
node_positions = {}
for dim_idx in range(n_dims):
    dim_total = dim_totals[dim_idx].sum()
    n_cats = len(levels[dim_idx])
    total_gap = gap_ratio * chart_height if n_cats > 1 else 0
    gap_size = total_gap / (n_cats - 1) if n_cats > 1 else 0
    y_top = margin_top
    for cat in levels[dim_idx]:
        height = dim_totals[dim_idx][cat] / dim_total * (chart_height - total_gap)
        node_positions[(dim_idx, cat)] = (y_top, y_top + height)
        y_top += height + gap_size

parallel_svg = '<g id="parallel-categories">'

# Ribbons between neighboring axes, split and colored by the first dimension
source_offsets = {key: top for key, (top, _) in node_positions.items()}
target_offsets = dict(source_offsets)
for dim_idx in range(n_dims - 1):
    source_dim, target_dim = DIMENSIONS[dim_idx], DIMENSIONS[dim_idx + 1]
    group_keys = list(dict.fromkeys([source_dim, target_dim, DIMENSIONS[0]]))
    flows = df.groupby(group_keys, sort=False)[ORDERS].sum().reset_index()
    flows["_order"] = [
        (
            levels[dim_idx].index(row[source_dim]),
            levels[dim_idx + 1].index(row[target_dim]),
            levels[0].index(row[DIMENSIONS[0]]),
        )
        for _, row in flows.iterrows()
    ]
    flows = flows.sort_values("_order")

    band_x0 = x_positions[dim_idx] + bar_width / 2 + (label_lanes[dim_idx] if dim_idx > 0 else 0)
    band_x1 = x_positions[dim_idx + 1] - bar_width / 2
    cx0 = band_x0 + 0.4 * (band_x1 - band_x0)
    cx1 = band_x0 + 0.6 * (band_x1 - band_x0)

    for _, row in flows.iterrows():
        source_cat, target_cat, flow_value = row[source_dim], row[target_dim], row[ORDERS]
        if not flow_value > 0:
            continue
        source_top, source_bottom = node_positions[(dim_idx, source_cat)]
        target_top, target_bottom = node_positions[(dim_idx + 1, target_cat)]
        source_height = flow_value / dim_totals[dim_idx][source_cat] * (source_bottom - source_top)
        target_height = flow_value / dim_totals[dim_idx + 1][target_cat] * (target_bottom - target_top)

        y0_top = source_offsets[(dim_idx, source_cat)]
        y1_top = target_offsets[(dim_idx + 1, target_cat)]
        y0_bottom = y0_top + source_height
        y1_bottom = y1_top + target_height
        path_d = (
            f"M {band_x0:.1f},{y0_top:.1f} "
            f"C {cx0:.1f},{y0_top:.1f} {cx1:.1f},{y1_top:.1f} {band_x1:.1f},{y1_top:.1f} "
            f"L {band_x1:.1f},{y1_bottom:.1f} "
            f"C {cx1:.1f},{y1_bottom:.1f} {cx0:.1f},{y0_bottom:.1f} {band_x0:.1f},{y0_bottom:.1f} Z"
        )
        parallel_svg += f'\n<path d="{path_d}" fill="{first_colors[row[DIMENSIONS[0]]]}" fill-opacity="{ribbon_opacity}" stroke="none"/>'
        source_offsets[(dim_idx, source_cat)] = y0_bottom
        target_offsets[(dim_idx + 1, target_cat)] = y1_bottom

# Axes: one segment per category, first dimension in its Imprint hue, the rest in muted ink
for dim_idx, dim_name in enumerate(DIMENSIONS):
    x = x_positions[dim_idx]
    parallel_svg += (
        f'\n<text x="{x:.0f}" y="{margin_top - 50:.0f}" text-anchor="middle" font-size="56" '
        f'font-weight="bold" {font} fill="{INK}">{str(dim_name).replace("&", "&amp;")}</text>'
    )
    for cat in levels[dim_idx]:
        y_top, y_bottom = node_positions[(dim_idx, cat)]
        fill = first_colors[cat] if dim_idx == 0 else INK_MUTED
        parallel_svg += (
            f'\n<rect x="{x - bar_width / 2:.1f}" y="{y_top:.1f}" width="{bar_width}" '
            f'height="{y_bottom - y_top:.1f}" fill="{fill}" stroke="{PAGE_BG}" stroke-width="2"/>'
        )
        if dim_idx == 0:
            label_x, anchor = x - bar_width / 2 - label_pad, "end"
        else:
            label_x, anchor = x + bar_width / 2 + label_pad, "start"
        parallel_svg += (
            f'\n<text x="{label_x:.0f}" y="{(y_top + y_bottom) / 2:.0f}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" font-size="{label_size}" {font} fill="{INK}">'
            f"{str(cat).replace('&', '&amp;')}</text>"
        )

# Legend: which dimension the ribbon colors follow
legend_y = HEIGHT - margin_bottom + 110
legend_text = f"{DIMENSIONS[0]}:".replace("&", "&amp;")
parallel_svg += (
    f'\n<text x="{margin_left:.0f}" y="{legend_y + 36:.0f}" font-size="44" font-weight="bold" '
    f'{font} fill="{INK}">{legend_text}</text>'
)
legend_x = margin_left + 300
legend_spacing = chart_width / max(4, len(levels[0]))
for idx, (cat, color) in enumerate(first_colors.items()):
    lx = legend_x + idx * legend_spacing
    parallel_svg += (
        f'\n<rect x="{lx:.0f}" y="{legend_y:.0f}" width="48" height="48" fill="{color}"/>'
        f'\n<text x="{lx + 68:.0f}" y="{legend_y + 36:.0f}" font-size="44" {font} '
        f'fill="{INK_SOFT}">{str(cat).replace("&", "&amp;")}</text>'
    )

parallel_svg += "\n</g>"
svg_with_parallel = base_svg.replace("</svg>", f"{parallel_svg}\n</svg>")

# Save
with open(f"plot-{THEME}.svg", "w") as f:
    f.write(svg_with_parallel)
cairosvg.svg2png(bytestring=svg_with_parallel.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ margin: 0; padding: 20px; background: {PAGE_BG}; font-family: sans-serif; }}
        .container {{ max-width: 100%; margin: 0 auto; }}
        object {{ width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <object type="image/svg+xml" data="plot-{THEME}.svg">
            Parallel categories diagram not supported
        </object>
    </div>
</body>
</html>""")
