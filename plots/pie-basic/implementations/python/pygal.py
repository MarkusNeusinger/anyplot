"""anyplot.ai
pie-basic: Basic Pie Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-28
"""

import math
import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
EXPLODE_PX = 80  # how far the largest slice is pulled out of the circle

# Columns
EXPENSE = "Expense category"  # role: category
SPENDING = "Monthly spending (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("expenses.csv")
df = pd.DataFrame(
    {
        EXPENSE: ["Housing", "Food", "Transportation", "Utilities", "Healthcare", "Entertainment"],
        SPENDING: [1850, 720, 560, 340, 280, 250],
    }
)

# Plot
title = "Household Budget · pie-basic · python · pygal · anyplot.ai"
n = len(title)
title_font_size = max(44, round(66 * 67 / n)) if n > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_colors=("#FFFFFF",) * len(df),
    stroke_width=2.5,
    opacity=1,  # pygal's default 0.7 washes out the palette and the white labels
    opacity_hover=1,
)

chart = pygal.Pie(
    width=2400,
    height=2400,
    style=custom_style,
    title=title,
    inner_radius=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=36,
    print_values=True,
    print_labels=False,
    print_values_position="center",
    value_formatter=lambda x: f"{x:.1f}%",
    margin=80,
    margin_bottom=120,
    truncate_legend=-1,
)

total = df[SPENDING].sum()
largest = df[SPENDING].idxmax()
start = 0.0  # share of the circle already used; pygal draws clockwise from the top

for i, (name, amount) in enumerate(zip(df[EXPENSE], df[SPENDING], strict=True)):
    share = amount / total * 100
    # Theme-adaptive stroke creates a clean gap between slices in both themes
    slice_data = {"value": share, "style": f"stroke: {PAGE_BG}; stroke-width: 4"}
    if i == largest:
        # Pull the largest slice out along its bisector
        mid = 2 * math.pi * (start + share / 2) / 100
        dx, dy = EXPLODE_PX * math.sin(mid), -EXPLODE_PX * math.cos(mid)
        slice_data["node"] = {"transform": f"translate({dx:.1f}, {dy:.1f})"}
    start += share
    chart.add(str(name), [slice_data])

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
