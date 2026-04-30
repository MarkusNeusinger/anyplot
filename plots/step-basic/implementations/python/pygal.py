""" anyplot.ai
step-basic: Basic Step Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-30
"""

import os
import sys


# Pop script dir so this file (pygal.py) doesn't shadow the installed pygal package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Monthly cumulative sales (in thousands)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_sales = [45, 92, 128, 165, 198, 256, 312, 378, 425, 489, 562, 635]

# Find month with peak month-on-month growth for storytelling emphasis
monthly_growth = [cumulative_sales[i] - cumulative_sales[i - 1] for i in range(1, len(cumulative_sales))]
peak_idx = monthly_growth.index(max(monthly_growth)) + 1  # Nov (index 10) — +$73K

# Build true step-chart data using pygal.XY coordinates.
# Pattern per data point i: (i, prev_val)[no dot] → (i, val)[dot] → (i+1, val)[no dot]
# This creates genuine vertical rises and horizontal holds — no diagonal approximation.
step_data = []
for i, (month, val) in enumerate(zip(months, cumulative_sales, strict=True)):
    if i > 0:
        # Bottom of vertical step: hold previous value up to this x position
        step_data.append({"value": (i, cumulative_sales[i - 1]), "node": {"r": 0}})

    # Actual data point — larger dot + rich tooltip label for interactivity
    increment = val - (cumulative_sales[i - 1] if i > 0 else 0)
    is_peak = i == peak_idx
    if is_peak:
        label = f"★ Peak growth — {month}: +${increment}K → ${val}K cumulative"
    else:
        label = f"{month}: ${val}K cumulative (+${increment}K)"
    step_data.append({"value": (i, val), "node": {"r": 22 if is_peak else 14}, "label": label})

    if i < len(months) - 1:
        # Horizontal hold: extend current value to the next x position
        step_data.append({"value": (i + 1, val), "node": {"r": 0}})

# Custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=56,
    value_font_size=40,
    stroke_width=3,
    opacity="0.18",
    opacity_hover="0.9",
)

# Chart — XY mode gives full control over x coordinates for true vertical step transitions
chart = pygal.XY(
    width=4800,
    height=2700,
    title="step-basic · pygal · anyplot.ai",
    x_title="Month",
    y_title="Cumulative Sales ($K)",
    style=custom_style,
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 8},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=False,
    fill=True,
    margin=120,
    x_value_formatter=lambda x: months[round(x)] if 0 <= round(x) <= 11 else "",
)

# Place x-axis tick labels at integer positions 0–11 (mapped to month names by formatter)
chart.x_labels = list(range(12))
chart.add("Cumulative Sales", step_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
