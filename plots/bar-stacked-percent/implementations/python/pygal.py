""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-08
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

countries = ["USA", "Germany", "China", "Brazil", "Japan", "Australia"]
renewable = [18, 46, 12, 84, 9, 28]
nuclear = [8, 6, 5, 1, 8, 9]
fossil = [74, 48, 83, 15, 83, 63]

percentages_renewable = []
percentages_nuclear = []
percentages_fossil = []

for i in range(len(countries)):
    total = renewable[i] + nuclear[i] + fossil[i]
    percentages_renewable.append(round(renewable[i] / total * 100, 1))
    percentages_nuclear.append(round(nuclear[i] / total * 100, 1))
    percentages_fossil.append(round(fossil[i] / total * 100, 1))

chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-stacked-percent · pygal · anyplot.ai",
    x_title="Country",
    y_title="Percentage (%)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:.0f}%",
    margin=50,
)

chart.x_labels = countries
chart.add("Renewable", percentages_renewable)
chart.add("Nuclear", percentages_nuclear)
chart.add("Fossil Fuels", percentages_fossil)

chart.range = (0, 100)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
