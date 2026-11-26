"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import os

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Theme-adaptive zone colors: pastel tints in light mode, vivid mid-tones in dark mode
ZONE_LEFT = "#C8EDF2" if THEME == "light" else "#163C42"  # cyan underfitting zone
ZONE_RIGHT = "#EDD4E7" if THEME == "light" else "#3B2234"  # rose overfitting zone

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COMPLEXITY = "Model Complexity"  # role: model_complexity
BIAS = "Bias²"  # role: bias_squared
VARIANCE = "Variance"  # role: variance
IRREDUCIBLE = "Irreducible ε"  # role: irreducible_error
TOTAL = "Total Error"  # role: total_error

# Data: replace this block with your own table, for example df = pd.read_csv("errors.csv")
complexity = np.linspace(0.5, 10, 100)
df = pd.DataFrame(
    {
        COMPLEXITY: complexity,
        BIAS: 4.0 / (1 + 0.8 * complexity),
        VARIANCE: 0.1 * complexity**1.5,
        IRREDUCIBLE: np.full_like(complexity, 0.5),
    }
)
df[TOTAL] = df[BIAS] + df[VARIANCE] + df[IRREDUCIBLE]

# Plot
title = "curve-bias-variance-tradeoff · python · pygal · anyplot.ai"

optimal = df.loc[df[TOTAL].idxmin()]
optimal_complexity = float(optimal[COMPLEXITY])
optimal_error = float(optimal[TOTAL])

# Axis bounds: a little beyond the data on x, headroom above the highest curve on y
x_min, x_max = 0.0, float(df[COMPLEXITY].max()) * 1.1
y_min, y_max = 0.0, round(float(df[TOTAL].max()) * 1.22, 1)

# Series order: zones (0,1) → Bias² (2=green) → Variance (3) → Total (4) → Irred (5) → vert line (6=red) → point (7=red)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=(ZONE_LEFT, ZONE_RIGHT, IMPRINT_PALETTE[0], IMPRINT_PALETTE[1], IMPRINT_PALETTE[2], IMPRINT_PALETTE[3])
    + (IMPRINT_PALETTE[4], IMPRINT_PALETTE[4]),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=COMPLEXITY,
    y_title="Prediction Error",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=30,
    truncate_legend=-1,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
    print_values=False,
)

# Zone fills: flat lines at the top of the axis with fill=True create shaded background rectangles
zone_top = y_max * 0.999
is_left = df[COMPLEXITY] <= optimal_complexity
is_right = df[COMPLEXITY] >= optimal_complexity
underfitting_fill = [(x_min, zone_top)] + [(float(x), zone_top) for x in df.loc[is_left, COMPLEXITY]]
overfitting_fill = [(float(x), zone_top) for x in df.loc[is_right, COMPLEXITY]] + [(x_max, zone_top)]
chart.add("← Underfitting Zone", underfitting_fill, fill=True, stroke_style={"width": 0}, show_dots=False)
chart.add("Overfitting Zone →", overfitting_fill, fill=True, stroke_style={"width": 0}, show_dots=False)

# Main curves (palette positions 1-4: green, lavender, blue, ochre)
bias_data = list(zip(df[COMPLEXITY].tolist(), df[BIAS].tolist(), strict=True))
variance_data = list(zip(df[COMPLEXITY].tolist(), df[VARIANCE].tolist(), strict=True))
total_data = list(zip(df[COMPLEXITY].tolist(), df[TOTAL].tolist(), strict=True))
irreducible_data = list(zip(df[COMPLEXITY].tolist(), df[IRREDUCIBLE].tolist(), strict=True))

chart.add("Bias² (decreasing ↘)", bias_data, stroke_style={"width": 7, "dasharray": "14, 8"}, show_dots=False)
chart.add("Variance (increasing ↗)", variance_data, stroke_style={"width": 7, "dasharray": "8, 5"}, show_dots=False)
chart.add("Total Error (U-shaped)", total_data, stroke_style={"width": 9}, show_dots=False)
chart.add(
    "Irreducible Error (constant)", irreducible_data, stroke_style={"width": 6, "dasharray": "4, 6"}, show_dots=False
)

# Vertical dashed line from the axis up to the minimum of the total error
chart.add(
    f"│ Optimal x={optimal_complexity:.1f}",
    [(optimal_complexity, y_min), (optimal_complexity, optimal_error)],
    stroke_style={"width": 4, "dasharray": "10, 8"},
    show_dots=False,
)

# Optimal point marker (palette position 5: semantic red)
optimal_point = [
    {
        "value": (optimal_complexity, optimal_error),
        "label": f"Optimal: x={optimal_complexity:.1f}, err={optimal_error:.2f}",
    }
]
chart.add(f"★ Optimal Point (x={optimal_complexity:.1f})", optimal_point, show_dots=True, dots_size=20, stroke=False)

# The Style's stroke_width reaches every path through the `.reactive` class and beats the per-series
# width inherited from the series group, so the widths are repeated on the paths themselves.
line_widths = {2: 7, 3: 7, 4: 9, 5: 6, 6: 4}
width_css = "".join(f".series.serie-{i} .line {{ stroke-width: {w}px !important; }}" for i, w in line_widths.items())
svg_bytes = chart.render().replace(b"</svg>", f"<style>{width_css}</style></svg>".encode(), 1)

# Direct curve annotations are SVG text elements injected after rendering.
# Plot-area bounds in pixels for pygal 3200x1800 with legend_at_bottom (measured from the render)
chart_left, chart_right, chart_top, chart_bottom = 250, 3155, 175, 1490
ann_font = 38
ann_style = f"font-family: Arial, sans-serif; font-size: {ann_font}px; font-weight: bold;"

# Curve labels sit at 80% of the complexity range, each just above its own curve
ann_x = float(df[COMPLEXITY].min() + 0.8 * (df[COMPLEXITY].max() - df[COMPLEXITY].min()))
ann_row = df.iloc[(df[COMPLEXITY] - ann_x).abs().argmin()]
ann_x = float(ann_row[COMPLEXITY])
labels = [
    # (text, color, data x, data y)
    (TOTAL, IMPRINT_PALETTE[2], ann_x, float(ann_row[TOTAL]) + 0.10),
    (VARIANCE, IMPRINT_PALETTE[1], ann_x, float(ann_row[VARIANCE]) + 0.10),
    (BIAS, IMPRINT_PALETTE[0], ann_x, float(ann_row[BIAS]) - 0.15),
    # Irreducible label sits at the middle of the x range, clear of the bias label
    (IRREDUCIBLE, IMPRINT_PALETTE[3], x_min + 0.41 * (x_max - x_min), float(df[IRREDUCIBLE].iloc[0]) + 0.35),
]
text_elements = []
for text, color, lx, ly in labels:
    px = int(chart_left + (lx - x_min) / (x_max - x_min) * (chart_right - chart_left))
    py = int(chart_bottom - (ly - y_min) / (y_max - y_min) * (chart_bottom - chart_top))
    text_elements.append(f'<text x="{px}" y="{py}" style="{ann_style} fill: {color};">{text}</text>')

# Formula annotation near the top of the plot area
formula_style = f"font-family: Arial, sans-serif; font-size: 34px; fill: {INK_MUTED};"
fx = int(chart_left + 0.5 * (chart_right - chart_left))
fy = int(chart_bottom - (0.94 * y_max - y_min) / (y_max - y_min) * (chart_bottom - chart_top))
text_elements.append(
    f'<text x="{fx}" y="{fy}" text-anchor="middle" style="{formula_style}">{TOTAL} = {BIAS} + {VARIANCE} + ε</text>'
)

svg_str = svg_bytes.decode("utf-8").replace("</svg>", "\n".join(text_elements) + "\n</svg>")

# Render the modified SVG to PNG so the annotations show in both themes
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")

# Interactive HTML (unmodified SVG: tooltips serve as annotations in the browser)
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_bytes)
