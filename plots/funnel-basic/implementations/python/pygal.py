""" anyplot.ai
funnel-basic: Basic Funnel Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-16
"""

import os

import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series is ALWAYS brand green (#009E73)
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# Data — sales conversion funnel, stages ordered largest (top) → smallest (bottom)
# Deterministic data, no random seed needed
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]
base_value = values[0]

# Style — pygal's Style carries every theme token. Font sizes are unitless and
# render straight onto the 3200-px source grid (see default-style-guide.md
# "Why the Native-pixel numbers look so much bigger").
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
    legend_font_size=48,
    value_font_size=44,
    tooltip_font_size=40,
    opacity=1,
)

# Plot — pygal's native Funnel chart; each stage is its own series so the
# segments carry distinct Imprint colors and the legend names every stage.
chart = pygal.Funnel(
    width=3200,
    height=1800,
    title="funnel-basic · python · pygal · anyplot.ai",
    style=custom_style,
    print_values=True,
    value_formatter=lambda v: f"{v:,.0f}  ({v / base_value * 100:.0f}%)",
    margin=50,
    margin_bottom=15,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=36,
    show_x_labels=False,
    show_y_labels=False,
    show_y_guides=False,
    truncate_legend=-1,
)

# Each stage added as a single-value series — the value (and conversion %) is
# printed on the segment via the value_formatter above.
for stage, value in zip(stages, values, strict=True):
    chart.add(stage, value)

# Save — theme-suffixed PNG (cairosvg) plus interactive HTML (pygal is interactive)
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
