"""anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import sys

import pandas as pd


# Temporarily remove current directory from path to avoid name collision with pygal module
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette, all eight positions in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
BAR_GAP = 0.8  # gap between bars, in percent of the total width
SEGMENT_GAP = 0.6  # gap between stacked segments, in percent of the bar height
LABEL_DX, LABEL_DY = 3.0, 3.0  # pygal draws a label right of and below its point; shift back to center it
MIN_LABEL_SHARE = 6  # segments below this percent of the bar stay unlabeled

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
totals = table.sum(axis=1)
usable = 100 - BAR_GAP * (len(table) - 1)
widths = totals / totals.sum() * usable
lefts = widths.cumsum() - widths + BAR_GAP * pd.Series(range(len(table)), index=table.index)
shares = table.div(totals, axis=0) * 100
bottoms = shares.cumsum(axis=1) - shares

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    value_label_font_size=40,
    value_colors=("white",) * len(table.columns),
    font_family="sans-serif",
    opacity=1,
    opacity_hover=1,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="marimekko-basic · python · pygal · anyplot.ai",
    x_title=f"{REGION} (bar width = share of total revenue)",
    y_title="Share within Region (%)",
    fill=True,
    stroke=True,
    stroke_style={"width": 0},
    show_dots=True,
    dots_size=0,
    print_labels=True,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, 100),
    xrange=(0, 100),
    y_labels=[0, 25, 50, 75, 100],
    value_formatter=lambda v: f"{v:.0f}%",
    legend_at_bottom=True,
    legend_box_size=36,
    truncate_label=-1,
    margin=50,
)
chart.x_labels = [{"label": region, "value": lefts[region] + widths[region] / 2} for region in table.index]

for product in table.columns:
    points = []
    for region in table.index:
        x0, x1 = lefts[region], lefts[region] + widths[region]
        y0, y1 = (
            bottoms.loc[region, product] + SEGMENT_GAP / 2,
            bottoms.loc[region, product] + shares.loc[region, product],
        )
        y1 -= SEGMENT_GAP / 2
        share = shares.loc[region, product]
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        corner = [(x0, y0), (xc, y0)]
        if share >= MIN_LABEL_SHARE and widths[region] > 6:
            # zero-area spike to the segment center carries the value label
            corner += [{"value": (xc - LABEL_DX, yc + LABEL_DY), "label": f"{share:.0f}%"}, (xc, y0)]
        points += corner + [(x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        points.append((None, None))
    points.pop()
    chart.add(str(product), points, allow_interruptions=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
