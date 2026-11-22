"""anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: pygal 3.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-18
"""

import os

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
BRAND = IMPRINT_PALETTE[0]  # significant coefficients
MUTED = INK_MUTED  # non-significant coefficients (theme-adaptive muted)

# Columns: set these to your table's column names
VARIABLE = "Variable"  # role: variable
COEFFICIENT = "Coefficient Estimate"  # role: coefficient
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
# Coefficients from a housing price regression model, 95% intervals (estimate ± 1.96 standard errors)
df = pd.DataFrame(
    {
        VARIABLE: [
            "Square Footage",
            "Number of Bedrooms",
            "Number of Bathrooms",
            "Garage Size",
            "Lot Size (acres)",
            "Age of Home (years)",
            "Distance to City Center",
            "School Rating",
            "Crime Rate Index",
            "Property Tax Rate",
        ],
        COEFFICIENT: [0.45, 0.12, 0.28, 0.18, 0.35, -0.22, -0.15, 0.25, -0.08, -0.05],
        CI_LOWER: [0.2932, -0.0564, 0.1624, 0.082, 0.154, -0.3572, -0.3852, 0.0932, -0.2956, -0.2264],
        CI_UPPER: [0.6068, 0.2964, 0.3976, 0.278, 0.546, -0.0828, 0.0852, 0.4068, 0.1356, 0.1264],
    }
)

# Plot: reads only df and the constants above
# Sort by coefficient so the rows read from the smallest to the largest estimate
table = df.sort_values(COEFFICIENT).reset_index(drop=True)
n_rows = len(table)
# Significant when the interval does not cross zero
significant = (table[CI_LOWER] > 0) | (table[CI_UPPER] < 0)

# Axis range from the intervals, with a margin on both sides
x_min, x_max = table[CI_LOWER].min(), table[CI_UPPER].max()
x_pad = 0.12 * (x_max - x_min)

# pygal colors series by position, so list one color per series in the order they are added
point_colors = (
    [BRAND, MUTED] if significant.any() and not significant.all() else [BRAND if significant.all() else MUTED]
)
series_colors = point_colors + [BRAND if sig else MUTED for sig in significant] + [INK_SOFT]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="coefficient-confidence · python · pygal · anyplot.ai",
    x_title=COEFFICIENT,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=False,
    show_x_guides=True,
    dots_size=14,
    stroke=False,
    xrange=(x_min - x_pad, x_max + x_pad),
    range=(0, n_rows + 1),
    margin_top=40,
    margin_bottom=40,
    margin_left=40,
    margin_right=60,
    spacing=24,
    y_labels=[{"value": i + 1, "label": name} for i, name in enumerate(table[VARIABLE])],
)

# Point series: significant first so it takes the brand green
rows = list(enumerate(zip(table[COEFFICIENT], table[CI_LOWER], table[CI_UPPER], significant, strict=True), start=1))
sig_points = [(coef, y) for y, (coef, _, _, sig) in rows if sig]
nonsig_points = [(coef, y) for y, (coef, _, _, sig) in rows if not sig]
if sig_points:
    chart.add("Significant (p < 0.05)", sig_points, color=BRAND, dots_size=14)
if nonsig_points:
    chart.add("Not Significant", nonsig_points, color=MUTED, dots_size=14)

# One unnamed line series per confidence interval
for y, (_, lower, upper, sig) in rows:
    chart.add(
        None,
        [(lower, y), (upper, y)],
        stroke=True,
        show_dots=False,
        stroke_style={"width": 4, "linecap": "round"},
        color=BRAND if sig else MUTED,
    )

# Vertical reference line at zero, full height of the rows
chart.add(
    "Zero Reference",
    [(0, 0), (0, n_rows + 1)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "8,4"},
    color=INK_SOFT,
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
