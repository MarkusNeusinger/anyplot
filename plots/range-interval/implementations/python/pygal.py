"""anyplot.ai
range-interval: Range Interval Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
TEMP_MIN = "Daily low (°C)"  # role: min_value
TEMP_MAX = "Daily high (°C)"  # role: max_value

# Data: replace this block with your own table, for example df = pd.read_csv("ranges.csv")
# Perth, Western Australia: average daily low and high per month (southern hemisphere, summer in Jan)
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        TEMP_MIN: [18, 18, 17, 14, 11, 9, 8, 8, 9, 11, 14, 16],
        TEMP_MAX: [31, 32, 30, 26, 22, 19, 18, 19, 21, 24, 27, 29],
    }
)

# Plot: pygal takes plain lists, built from df
span = (df[TEMP_MAX] - df[TEMP_MIN]).tolist()

# The first series is an invisible base up to each minimum, so the visible bar floats from min to max
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=("transparent", *IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

axis_low = int(df[TEMP_MIN].min() // 5 * 5) - 5
axis_high = int(-(-df[TEMP_MAX].max() // 5) * 5) + 5

chart = pygal.StackedBar(
    width=3200,
    height=1800,
    style=style,
    title="range-interval · python · pygal · anyplot.ai",
    x_title=MONTH,
    y_title="Temperature (°C)",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    range=(axis_low, axis_high),
    spacing=30,
    margin=60,
)
chart.x_labels = df[MONTH].tolist()
chart.add(TEMP_MIN, df[TEMP_MIN].tolist())
chart.add("Range low to high (°C)", span)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
