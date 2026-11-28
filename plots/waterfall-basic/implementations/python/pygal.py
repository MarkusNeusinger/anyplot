"""anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: pygal 3.1.3 | Python 3.13.14
Quality: 89/100 | Updated: 2026-08-04
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (Imprint palette — see default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (full list; the waterfall uses the semantic picks below)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Semantic exception (default-style-guide.md "Color Philosophy"): sentiment/polarity
# categories map to their expected colors rather than plain ordinal position.
BRAND_GREEN = IMPRINT_PALETTE[0]  # Imprint position 1 — gain / increase
SEMANTIC_RED = IMPRINT_PALETTE[4]  # Imprint position 5 — deferred loss/error anchor — decrease
NEUTRAL = INK  # theme-adaptive semantic anchor — totals / baseline

# Columns: set these to your table's column names
STEP = "Category"  # role: category
AMOUNT = "Amount ($K)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("bridge.csv").
# First row = start total, last row = end total (recomputed from the changes), rows between = changes.
df = pd.DataFrame(
    {
        STEP: [
            "Q1 Revenue",
            "Product Sales",
            "Services",
            "COGS",
            "Operating Exp",
            "Other Income",
            "Taxes",
            "Net Income",
        ],
        AMOUNT: [500, 150, 80, -180, -120, 25, -68, 387],
    }
)

# Plot: per-bar geometry derived from df
n_bars = len(df)
changes = df[AMOUNT].iloc[1:-1].tolist()
running_totals = [df[AMOUNT].iloc[0]]
for val in changes:
    running_totals.append(running_totals[-1] + val)
running_totals.append(running_totals[-1])  # the end total equals the running total after the last change
# Series slot per bar: 0 = total, 1 = increase, 2 = decrease
bar_types = [0] + [1 if val >= 0 else 2 for val in changes] + [0]
bar_bottoms = [0] + [min(running_totals[i - 1], running_totals[i]) for i in range(1, n_bars - 1)] + [0]
bar_heights = [running_totals[0]] + [abs(val) for val in changes] + [running_totals[-1]]
display_values = [running_totals[0]] + changes + [running_totals[-1]]


class WaterfallChart(pygal.StackedBar):
    """StackedBar with dashed connector lines between waterfall steps.

    pygal has no native bar+line combo chart, so the connectors are drawn
    directly on the SVG plot layer, reusing the exact view/margin math
    StackedBar._bar() uses internally so the connector endpoints land
    pixel-exact on the bar edges.
    """

    def __init__(self, *args, connector_levels=None, connector_color="#000", **kwargs):
        self._connector_levels = connector_levels or []
        self._connector_color = connector_color
        super().__init__(*args, **kwargs)

    def _plot(self):
        super()._plot()
        n = self._len
        width_full = (self.view.x(1) - self.view.x(0)) / n
        margin = width_full * self._series_margin
        bar_width = width_full - 2 * margin
        node = self.svg.node(self.nodes["plot"], class_="waterfall-connectors")
        for i, level in enumerate(self._connector_levels):
            if level is None:
                continue
            x_right = self.view.x(i / n) + margin + bar_width
            x_left = self.view.x((i + 1) / n) + margin
            y = self.view.y(level)
            self.svg.line(
                node,
                [(x_right, y), (x_left, y)],
                style=(f"stroke:{self._connector_color};stroke-width:3;stroke-dasharray:14,10;fill:none;opacity:0.85"),
            )


# Theme-adaptive Style — first categorical series is always Imprint position 1
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=("transparent", NEUTRAL, BRAND_GREEN, SEMANTIC_RED),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_label_font_size=36,  # pygal renders print_labels() text (our "+$150K"
    # strings) through this separate key, NOT value_font_size — easy to miss since
    # it defaults to 10px regardless of the other sizes
    stroke_width=2.5,
    opacity="1",  # pygal defaults to 0.7, which blends fills toward the page color
    opacity_hover="1",
)

chart = WaterfallChart(
    width=3200,
    height=1800,
    style=custom_style,
    title="waterfall-basic · python · pygal · anyplot.ai",
    x_title=STEP,
    y_title=AMOUNT,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,  # force Total/Increase/Decrease onto one row
    # instead of pygal's default ceil(sqrt(n)) grid, which scattered them 2x2
    show_y_guides=True,
    show_x_guides=False,
    print_labels=True,  # show the "+$150K" / "-$180K" strings from each point's
    # "label" key — plain print_values would print the raw stacked-segment height
    # instead (and, via StackedBar's none_to_zero adapter, a stray "0" for every
    # other series' empty slot at that category)
    print_values_position="center",
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=25,
    margin=60,
    margin_bottom=380,
    spacing=34,  # extra breathing room so the legend row doesn't crowd the x_title
    connector_levels=running_totals[:-1],
    connector_color=INK_MUTED,
)

# Set x-axis labels (category + running total)
labels_with_totals = [f"{cat} (${running_totals[i]}K)" for i, cat in enumerate(df[STEP])]
chart.x_labels = labels_with_totals

# Build data series: spacer (invisible), then one list per slot (total, increase, decrease)
label_signs = ["", "+", "-"]
spacer_data = []
slot_data = [[], [], []]

for i in range(n_bars):
    bottom = bar_bottoms[i]
    btype = bar_types[i]
    spacer_data.append({"value": bottom if bottom > 0 else None, "label": ""})
    for slot, data in enumerate(slot_data):
        if slot == btype:
            data.append({"value": bar_heights[i], "label": f"{label_signs[slot]}${abs(display_values[i])}K"})
        else:
            data.append({"value": None})

total_data, positive_data, negative_data = slot_data

# Add series in stack order (bottom to top). Series order fixes the Style.colors
# index: spacer(0)=transparent, Total(1)=neutral, Increase(2)=brand green
# (Imprint position 1 — semantic "gain"), Decrease(3)=matte red (Imprint
# position 5 — semantic "loss"), per default-style-guide.md Semantic Exception.
chart.add(None, spacer_data, stroke_style={"width": 0}, show_legend=False)
chart.add("Total", total_data)
chart.add("Increase", positive_data)
chart.add("Decrease", negative_data)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
