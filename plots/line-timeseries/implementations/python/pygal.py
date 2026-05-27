""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-09
"""

import os
import random
import sys
from datetime import datetime, timedelta


# Ensure site-packages is in path before current directory to avoid shadowing
site_packages = next((p for p in sys.path if "site-packages" in p), None)
if site_packages and sys.path[0] == os.path.dirname(__file__):
    sys.path.remove(sys.path[0])
    sys.path.insert(0, site_packages)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Seed for reproducibility
random.seed(42)

# Generate realistic daily stock price data for one year
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(365)]

# Simulate stock price with trend and volatility
price = 150.0
prices = []
for _ in range(365):
    change = random.gauss(0.1, 2.5)
    price = max(100, price + change)
    prices.append(round(price, 2))

# Custom style for 4800x2700 canvas
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
    stroke_width=6,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-timeseries · pygal · anyplot.ai",
    x_title="Date",
    y_title="Stock Price (USD)",
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=45,
    show_legend=True,
    legend_at_bottom=True,
    truncate_legend=-1,
    show_dots=False,
    margin=100,
)

# Add data series
chart.add("ACME Corp Stock", prices)

# Set x-axis labels - show first of each month only
x_labels = []
x_labels_major = []
for d in dates:
    if d.day == 1:
        x_labels.append(d.strftime("%b %Y"))
        x_labels_major.append(d.strftime("%b %Y"))
    else:
        x_labels.append("")

chart.x_labels = x_labels
chart.x_labels_major = x_labels_major

# Save as PNG and HTML
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
