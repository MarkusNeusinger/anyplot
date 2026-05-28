""" anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data
np.random.seed(42)
complexity = np.linspace(0.5, 10, 100)
bias_squared = 4.0 / (1 + 0.8 * complexity)
variance = 0.1 * complexity**1.5
irreducible_error = np.full_like(complexity, 0.5)
total_error = bias_squared + variance + irreducible_error

optimal_idx = int(np.argmin(total_error))
optimal_complexity = float(complexity[optimal_idx])
optimal_error = float(total_error[optimal_idx])

title = "curve-bias-variance-tradeoff · python · pygal · anyplot.ai"
title_fontsize = 66  # 58 chars < 67 threshold, no scaling needed

# Palette: zones first (behind curves), then data series in canonical anyplot order
# Zones get positions 1–2; Bias² gets position 3 = #009E73 (first data/categorical series)
ZONE_LEFT = "#2ABCCD"  # cyan – underfitting zone fill
ZONE_RIGHT = "#954477"  # rose  – overfitting zone fill

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(ZONE_LEFT, ZONE_RIGHT, "#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"),
    title_font_size=title_fontsize,
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
    x_title="Model Complexity",
    y_title="Prediction Error  |  Total = Bias² + Variance + ε",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=30,
    truncate_legend=-1,
    range=(0, 5.0),
    xrange=(0, 11),
    print_values=False,
)

# Zone fills — shaded background regions drawn first so curves appear on top.
# A flat line at y=5.0 with fill=True creates a filled rectangle from y=0 to y=5.
underfitting_fill = [(0.0, 5.0)] + [(float(x), 5.0) for x in complexity[: optimal_idx + 1]]
overfitting_fill = [(float(x), 5.0) for x in complexity[optimal_idx:]] + [(11.0, 5.0)]
chart.add("← Underfitting Zone", underfitting_fill, fill=True, stroke=False, show_dots=False)
chart.add("Overfitting Zone →", overfitting_fill, fill=True, stroke=False, show_dots=False)

# Main curves (palette positions 3–6: green, lavender, blue, ochre)
bias_data = [(float(x), float(y)) for x, y in zip(complexity, bias_squared, strict=True)]
variance_data = [(float(x), float(y)) for x, y in zip(complexity, variance, strict=True)]
total_data = [(float(x), float(y)) for x, y in zip(complexity, total_error, strict=True)]
irreducible_data = [(float(x), float(y)) for x, y in zip(complexity, irreducible_error, strict=True)]

chart.add("Bias² (decreasing ↘)", bias_data, stroke_style={"width": 7, "dasharray": "14, 8"}, show_dots=False)
chart.add("Variance (increasing ↗)", variance_data, stroke_style={"width": 7, "dasharray": "8, 5"}, show_dots=False)
chart.add("Total Error (U-shaped)", total_data, stroke_style={"width": 9}, show_dots=False)
chart.add(
    "Irreducible Error (constant)", irreducible_data, stroke_style={"width": 6, "dasharray": "4, 6"}, show_dots=False
)

# Optimal point marker (palette position 7: #AE3030 semantic red)
optimal_point = [
    {
        "value": (optimal_complexity, optimal_error),
        "label": f"Optimal: complexity={optimal_complexity:.1f}, error={optimal_error:.2f}",
    }
]
chart.add(f"★ Optimal Point (x={optimal_complexity:.1f})", optimal_point, show_dots=True, dots_size=20, stroke=False)

# Save PNG and HTML (pygal is interactive)
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
