"""anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
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

# Imprint palette, all eight positions in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
GAP = 0.012  # empty share of the x range between neighbouring bars

# Columns: set these to your table's column names
REGION = "Region"  # role: x_category
PRODUCT = "Product line"  # role: y_category
REVENUE = "Revenue (USD M)"  # role: value

# Data
regions = ["North America", "Europe", "Asia Pacific", "Latin America", "MEA"]
revenue = {
    "Enterprise": [180, 140, 200, 60, 40],
    "Consumer": [120, 130, 180, 70, 45],
    "SMB": [90, 70, 90, 35, 25],
    "Government": [60, 40, 50, 15, 10],
}
df = pd.DataFrame(
    [(region, product, v) for product, vals in revenue.items() for region, v in zip(regions, vals, strict=True)],
    columns=[REGION, PRODUCT, REVENUE],
)

# Plot
table = df.pivot_table(index=REGION, columns=PRODUCT, values=REVENUE, sort=False, aggfunc="sum")
n_bars, n_stack = table.shape
totals = table.sum(axis=1)

# Bar geometry on a 0..1 x range: width follows the bar total, gaps sit between bars
widths = totals / totals.sum() * (1 - GAP * (n_bars - 1))
lefts = widths.cumsum() - widths + GAP * pd.Series(range(n_bars), index=widths.index)
centers = lefts + widths / 2
shares = table.div(totals, axis=0) * 100
tops = shares.cumsum(axis=1)
label_of_center = {round(float(c), 6): name for c, name in zip(centers, table.index, strict=True)}

# Each segment is a filled area from the baseline up to its cumulative top. The topmost
# segment of every bar is added first, so the segments below paint over it.
order = list(reversed(range(n_stack)))
colors = tuple(IMPRINT_PALETTE[j % len(IMPRINT_PALETTE)] for j in order for _ in range(n_bars))

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=colors + (INK,),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    opacity="1",
    opacity_hover="1",
    stroke_opacity="1",
    stroke_opacity_hover="1",
    font_family="sans-serif",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=style,
    fill=True,
    show_dots=False,
    stroke_style={"width": 3},
    title="marimekko-basic · python · pygal · anyplot.ai",
    x_title=f"{REGION} (bar width = share of total revenue)",
    y_title=f"Share within {REGION.lower()} (%)",
    show_x_guides=False,
    show_y_guides=True,
    range=(0, 100),
    xrange=(0, 1),
    x_labels=[float(c) for c in centers],
    y_labels=[0, 25, 50, 75, 100],
    x_value_formatter=lambda v: label_of_center.get(round(v, 6), ""),
    value_formatter=lambda v: f"{v:.0f}%",
    legend_box_size=36,
    margin=40,
    css=["file://style.css", "file://graph.css", f"inline:.line{{stroke:{PAGE_BG} !important}}"],
)

for j in order:
    for i in range(n_bars):
        x0, x1, top = lefts.iloc[i], lefts.iloc[i] + widths.iloc[i], tops.iloc[i, j]
        chart.add(table.columns[j] if i == 0 else None, [(x0, 0), (x0, top), (x1, top), (x1, 0)])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
