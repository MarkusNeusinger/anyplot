"""anyplot.ai
bar-basic: Basic Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import os
import sys


# Prevent this file from shadowing the installed pygal package
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]

import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CHANNEL = "Channel"  # role: category
VISITS = "Visits (Q4 2025)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
df = pd.DataFrame(
    {
        CHANNEL: ["Organic Search", "Direct", "Social Media", "Email", "Referral", "Paid Ads", "Affiliates"],
        VISITS: [142500, 98700, 87300, 53200, 41800, 72600, 18900],
    }
)

# Plot: reads only df and the constants above
ranked = df.sort_values(VISITS, ascending=False)
categories = ranked[CHANNEL].tolist()
values = ranked[VISITS].tolist()
leader = ranked.iloc[0]
share = leader[VISITS] / ranked[VISITS].sum()
top = ranked[VISITS].max()

# Leader in brand green, the rest in the muted token
bar_data = [{"value": v, "color": IMPRINT_PALETTE[0] if i == 0 else INK_MUTED} for i, v in enumerate(values)]

# Y ticks: six even steps from zero up to the first multiple of 30,000 above the maximum
step = 30000
y_ticks = [step * k for k in range(int(top // step) + 2)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    colors=IMPRINT_PALETTE,
    value_colors=(INK,),
    opacity="1",
    opacity_hover="1",
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=42,
    stroke_width=2.5,
)

chart = pygal.Bar(
    width=3200,
    height=1800,
    title=f"bar-basic · python · pygal · anyplot.ai\n{leader[CHANNEL]} leads Q4 2025 traffic at {share:.0%} share",
    x_title=CHANNEL,
    y_title=VISITS,
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

chart.y_labels = y_ticks
chart.x_labels = categories
chart.add(VISITS, bar_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
