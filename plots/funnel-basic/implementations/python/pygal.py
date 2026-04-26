"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: pygal | Python 3.13
Quality: pending | Created: 2026-04-26
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette — first stage is brand green (#009E73)
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — sales funnel example from the specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]
base = values[0]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=44,
    label_font_size=28,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=32,
    value_label_font_size=32,
    tooltip_font_size=22,
    value_colors=(INK,) * len(stages),
    stroke_width=2,
    opacity=0.95,
)

chart = pygal.Funnel(
    width=4800,
    height=2700,
    title="Sales Funnel · funnel-basic · pygal · anyplot.ai",
    style=custom_style,
    print_values=False,
    print_labels=True,
    margin_top=140,
    margin_bottom=40,
    margin_left=40,
    margin_right=40,
    show_legend=False,
    show_y_labels=False,
    show_x_labels=False,
    show_y_guides=False,
    show_x_guides=False,
    spacing=20,
)

for stage, value in zip(stages, values, strict=True):
    chart.add(stage, [{"value": value, "label": f"{stage}  ·  {value:,}  ·  {value / base * 100:.0f}%"}])

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
