"""anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-27
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — balanced multi-asset portfolio with individual holdings
holdings = {
    "Equities": {"US Large Cap": 25.0, "US Mid Cap": 10.0, "International Developed": 12.0, "Emerging Markets": 8.0},
    "Fixed Income": {"US Treasury": 15.0, "Corporate Bonds": 8.0, "Municipal Bonds": 5.0},
    "Alternatives": {"Real Estate": 7.0, "Commodities": 5.0, "Private Equity": 5.0},
}

title = "pie-portfolio-interactive · python · pygal · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_font_size = max(44, round(66 * ratio))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    tooltip_font_size=36,
)

# Each holding is a separate interactive slice, grouped by category color
chart = pygal.Pie(
    width=2400,
    height=2400,
    style=custom_style,
    inner_radius=0.35,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=40,
    title=title,
    print_values=True,
    value_formatter=lambda x: f"{x:.1f}%",
    margin=80,
    margin_bottom=200,
    spacing=20,
)

for category, assets in holdings.items():
    chart.add(category, [{"value": weight, "label": f"{name}: {weight:.1f}%"} for name, weight in assets.items()])

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
