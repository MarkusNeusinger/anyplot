""" anyplot.ai
bar-basic: Basic Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import os
import sys


# Prevent this file from shadowing the installed pygal package
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND = IMPRINT_PALETTE[0]

# Data — website traffic by channel (Q4 2025), sorted descending for ranking readability
categories_raw = ["Organic Search", "Direct", "Social Media", "Email", "Referral", "Paid Ads", "Affiliates"]
values_raw = [142500, 98700, 87300, 53200, 41800, 72600, 18900]

sorted_pairs = sorted(zip(values_raw, categories_raw, strict=False), reverse=True)
values, categories = zip(*sorted_pairs, strict=False)
values, categories = list(values), list(categories)

max_idx = 0  # descending sort puts leader first
total = sum(values)

# Per-bar data — highlight leader with brand green, muted for the rest
bar_data = [{"value": v, "color": BRAND if i == max_idx else INK_MUTED} for i, v in enumerate(values)]
bar_data[max_idx]["formatter"] = lambda x: f"★ {x:,.0f} ({x / total:.0%} of total)"

# Style — title is 40 chars (<67), so title_font_size stays at 66
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Chart
chart = pygal.Bar(
    width=3200,
    height=1800,
    title="bar-basic · python · pygal · anyplot.ai\nOrganic Search leads Q4 2025 traffic at 28% share",
    x_title="Channel",
    y_title="Visits (Q4 2025)",
    style=custom_style,
    show_legend=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:,.0f}",
    show_y_guides=True,
    show_x_guides=False,
    margin=20,
    margin_bottom=60,
    margin_left=30,
    margin_right=30,
    rounded_bars=6,
    truncate_label=-1,
    x_label_rotation=0,
    show_minor_y_labels=False,
    y_labels_major_every=1,
)

chart.y_labels = [0, 30000, 60000, 90000, 120000, 150000]
chart.x_labels = categories
chart.add("Visits", bar_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
