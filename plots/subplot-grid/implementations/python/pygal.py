"""anyplot.ai
subplot-grid: Subplot Grid Layout
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
CATEGORY = "Category"  # role: extra
ORDERS = "Orders per day"  # role: extra
REVENUE = "Revenue ($K)"  # role: y
AD_SPEND = "Ad spend ($K)"  # role: extra
ROI = "ROI (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("shop_days.csv")
# One row per trading day of an online shop: 20 days in each of the 12 months.
rng = np.random.default_rng(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
categories = ["Electronics", "Apparel", "Home", "Sports", "Books"]
month_col = np.repeat(months, 20)
trend = np.repeat(np.linspace(1.0, 1.9, len(months)), 20)
orders = np.clip(rng.normal(150, 35, len(month_col)) * trend / 1.4, 40, None).round()
category_col = rng.choice(categories, size=len(month_col), p=[0.34, 0.24, 0.2, 0.13, 0.09])
ad_spend = rng.uniform(5, 50, len(month_col))
df = pd.DataFrame(
    {
        MONTH: month_col,
        CATEGORY: category_col,
        ORDERS: orders,
        REVENUE: orders * rng.normal(0.9, 0.08, len(month_col)),
        AD_SPEND: ad_spend,
        ROI: ad_spend * 0.12 + rng.normal(0, 1.5, len(month_col)),
    }
)

# Plot: pygal has no subplot support, so each cell is its own chart and the four SVGs
# are nested into one canvas SVG that also carries the figure title.
CANVAS_W, CANVAS_H = 3200, 1800
MARGIN, GAP, TITLE_H = 60, 40, 170
cell_w = (CANVAS_W - 2 * MARGIN - GAP) // 2
cell_h = (CANVAS_H - TITLE_H - MARGIN - GAP) // 2

fig_title = "subplot-grid · python · pygal · anyplot.ai"
title_size = round(78 * min(1.0, 67 / len(fig_title)))


def cell_style():
    return Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK_SOFT,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=IMPRINT_PALETTE,
        font_family="sans-serif",
        title_font_size=40,
        label_font_size=32,
        major_label_font_size=28,
        legend_font_size=28,
        value_font_size=24,
        stroke_width=4,
        opacity=0.85,
        opacity_hover=1.0,
    )


def make_cell(chart_class, title, x_title, y_title):
    return chart_class(
        width=cell_w,
        height=cell_h,
        style=cell_style(),
        title=title,
        x_title=x_title,
        y_title=y_title,
        show_legend=False,
        show_y_guides=True,
        show_x_guides=False,
        truncate_label=-1,
    )


# Top-left: line chart of monthly revenue
monthly = df.groupby(MONTH, sort=False)[REVENUE].sum()
line_chart = make_cell(pygal.Line, "Monthly revenue", MONTH, REVENUE)
line_chart.dots_size = 8
line_chart.x_labels = monthly.index.tolist()
line_chart.add("Revenue", monthly.tolist())

# Top-right: bar chart of revenue by category
by_category = df.groupby(CATEGORY)[REVENUE].sum().sort_values(ascending=False)
bar_chart = make_cell(pygal.Bar, "Revenue by category", CATEGORY, REVENUE)
bar_chart.spacing = 20
bar_chart.x_labels = by_category.index.tolist()
bar_chart.add("Revenue", by_category.tolist())

# Bottom-left: scatter of ad spend against ROI
scatter_chart = make_cell(pygal.XY, "Ad spend vs return", AD_SPEND, ROI)
scatter_chart.show_x_guides = True
scatter_chart.stroke = False
scatter_chart.dots_size = 7
scatter_chart.add("Days", list(zip(df[AD_SPEND].tolist(), df[ROI].tolist(), strict=True)))

# Bottom-right: histogram of daily orders
counts, edges = np.histogram(df[ORDERS].dropna(), bins=int(np.sqrt(len(df))))
hist_chart = make_cell(pygal.Histogram, "Daily order volume", ORDERS, "Days")
hist_chart.add(
    "Days", [(int(c), float(lo), float(hi)) for c, lo, hi in zip(counts, edges[:-1], edges[1:], strict=True)]
)

# Nest the four chart SVGs into a single canvas SVG
cells = [line_chart, bar_chart, scatter_chart, hist_chart]
nested = []
for i, chart in enumerate(cells):
    x = MARGIN + (i % 2) * (cell_w + GAP)
    y = TITLE_H + (i // 2) * (cell_h + GAP)
    chart.disable_xml_declaration = True
    svg = chart.render(is_unicode=True)
    svg = svg.replace("<svg ", f'<svg x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" ', 1)
    nested.append(svg)

canvas_svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}">'
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAGE_BG}"/>'
    f'<text x="{CANVAS_W // 2}" y="{TITLE_H - 70}" text-anchor="middle" font-family="sans-serif" '
    f'font-size="{title_size}" font-weight="bold" fill="{INK}">{fig_title}</text>'
    f"{''.join(nested)}</svg>"
)

# Save
cairosvg.svg2png(bytestring=canvas_svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{fig_title}</title></head>"
        f"<body style='margin:0;background:{PAGE_BG}'>"
        f"<div style='max-width:{CANVAS_W}px;margin:0 auto'>"
        f"{canvas_svg.replace('<svg xmlns', '<svg style="width:100%;height:auto" xmlns', 1)}"
        "</div></body></html>"
    )
