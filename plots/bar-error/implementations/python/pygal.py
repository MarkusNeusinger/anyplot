"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, the single series takes position 1
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
GROUP = "Treatment Group"  # role: category
RESPONSE = "Response Value (units)"  # role: value
SD = "Standard deviation (units)"  # role: error

# Data: replace this block with your own table, for example df = pd.read_csv("experiment.csv")
# Mean response per group with ±1 standard deviation, control group first
df = pd.DataFrame(
    {
        GROUP: ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"],
        RESPONSE: [45.2, 62.8, 78.3, 55.1, 71.5],
        SD: [8.5, 12.3, 9.7, 15.2, 11.8],
    }
)

# Plot: reads only df and the constants above
top = (df[RESPONSE] + df[SD]).max()
bars = [
    None
    if pd.isna(mean)
    else {"value": float(mean)}
    if pd.isna(err)
    else {"value": float(mean), "ci": {"low": float(mean - err), "high": float(mean + err)}}
    for mean, err in zip(df[RESPONSE], df[SD], strict=True)
]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,  # axis titles and error bars (pygal strokes .ci with foreground)
    foreground_strong=INK,
    foreground_subtle=RULE,  # y guides
    colors=IMPRINT_PALETTE,
    font_family="DejaVu Sans, Verdana, sans-serif",
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    opacity=1,
    stroke_width=5,
    guide_stroke_dasharray="1,0",
    major_guide_stroke_dasharray="1,0",
)

chart = pygal.Bar(
    width=3200,
    height=1800,
    style=custom_style,
    title="bar-error · python · pygal · anyplot.ai",
    x_title=GROUP,
    y_title=RESPONSE,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=1,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    range=(0, top * 1.15),
    include_x_axis=True,
    spacing=40,
    margin=100,
    margin_bottom=120,
    margin_left=160,
    margin_top=120,
)

chart.x_labels = df[GROUP].astype(str).tolist()
chart.add("Mean ± 1 SD (error bars)", bars)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
