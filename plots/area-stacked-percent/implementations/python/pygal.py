"""anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order, one per category
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
DEVICE = "Device category"  # role: category
UNITS = "Units sold (millions)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("device_sales.csv")
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
market_size = [2100, 2200, 2000, 2300, 2200, 2400, 2500]  # all devices sold that year, million units
share_percent = {
    "Smartphones": [60, 59, 57, 56, 55, 54, 53],
    "Laptops": [10, 10, 11, 10, 9, 9, 9],
    "Tablets": [14, 14, 15, 14, 14, 13, 13],
    "Wearables": [10, 11, 11, 14, 16, 18, 19],
    "Accessories": [6, 6, 6, 6, 6, 6, 6],
}
df = pd.DataFrame(
    [
        (year, device, share * size / 100)
        for device, shares in share_percent.items()
        for year, share, size in zip(years, shares, market_size, strict=True)
    ],
    columns=[YEAR, DEVICE, UNITS],
)

# Plot: normalise each time point to 100 % of its total
table = df.pivot_table(index=YEAR, columns=DEVICE, values=UNITS, aggfunc="sum", sort=False)
percent = table.div(table.sum(axis=1), axis=0) * 100

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT_PALETTE,
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=48,
    value_font_size=36,
    opacity=1,
    opacity_hover=1,
    stroke_width=3,
)

chart = pygal.StackedLine(
    width=3200,
    height=1800,
    style=custom_style,
    title="area-stacked-percent · python · pygal · anyplot.ai",
    x_title=YEAR,
    y_title="Share of total (%)",
    fill=True,
    stack_from_top=False,
    range=(0, 100),
    include_x_axis=True,
    y_labels=[0, 20, 40, 60, 80, 100],
    value_formatter=lambda share: f"{share:.0f}%",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(percent.columns),
    legend_box_size=40,
    truncate_legend=-1,
    dots_size=6,
    spacing=24,
    margin=40,
)

chart.x_labels = [str(year) for year in percent.index]
for device in percent.columns:
    chart.add(str(device), [None if pd.isna(share) else float(share) for share in percent[device]])

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
