"""anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-22
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one position per component, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT = "Product category"  # role: component
REVENUE = "Revenue ($K)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 4,
        PRODUCT: ["Electronics"] * 4 + ["Furniture"] * 4 + ["Clothing"] * 4 + ["Accessories"] * 4,
        REVENUE: [180, 95, 140, 220, 45, 130, 85, 75, 55, 60, 145, 90, 32, 45, 38, 115],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=QUARTER, columns=PRODUCT, values=REVENUE, sort=False)
totals = table.sum(axis=1)

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=48,
    value_colors=(INK,) * len(IMPRINT_PALETTE),
    value_label_colors=(INK,) * len(IMPRINT_PALETTE),
    stroke_width=2.5,
)

chart = pygal.StackedBar(
    width=3200,
    height=1800,
    style=style,
    title="bar-stacked-labeled · python · pygal · anyplot.ai",
    x_title=QUARTER,
    y_title=REVENUE,
    show_y_guides=True,
    show_x_guides=False,
    print_values=True,
    print_values_position="top",
    formatter=lambda v: "",
    range=(0, totals.max() * 1.15),
    margin=60,
    spacing=40,
)
chart.x_labels = table.index.tolist()

# Segments carry no labels; the last series carries each stack's total, drawn above the stack
for i, component in enumerate(table.columns):
    values = table[component].tolist()
    if i == len(table.columns) - 1:
        values = [{"value": v, "formatter": lambda _, t=t: f"${t:,.0f}K"} for v, t in zip(values, totals, strict=True)]
    chart.add(str(component), values)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
