""" anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-22
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


# Restore path
sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
GRID = "#C9C7BD" if THEME == "light" else "#3A3A35"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Mean decrease in R² score"  # role: importance_mean
IMPORTANCE_STD = "Std of decrease across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("importance.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "Year Built",
            "Bathrooms",
            "Garage Size",
            "Lot Area",
            "Bedrooms",
            "Basement Area",
            "Total Rooms",
            "Living Area",
            "Neighborhood",
            "Overall Quality",
        ],
        IMPORTANCE: [0.002, 0.008, 0.015, 0.024, 0.032, 0.048, 0.067, 0.095, 0.128, 0.185],
        IMPORTANCE_STD: [0.003, 0.005, 0.008, 0.011, 0.014, 0.018, 0.022, 0.028, 0.035, 0.042],
    }
)

# Plot: reads only df and the constants above
# pygal draws the first label at the bottom, so ascending order puts the highest importance on top
table = df.dropna(subset=[IMPORTANCE]).sort_values(IMPORTANCE, ascending=True).reset_index(drop=True)
means = table[IMPORTANCE].astype(float)
stds = table[IMPORTANCE_STD].astype(float).fillna(0)

# Imprint sequential ramp (green -> blue) mapped to importance
SEQ_START, SEQ_END = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]
span = means.max() - means.min()
bar_colors = []
for mean in means:
    t = (mean - means.min()) / span if span else 0.0
    channels = [
        round(int(SEQ_START[i : i + 2], 16) + (int(SEQ_END[i : i + 2], 16) - int(SEQ_START[i : i + 2], 16)) * t)
        for i in (1, 3, 5)
    ]
    bar_colors.append(f"#{channels[0]:02X}{channels[1]:02X}{channels[2]:02X}")

lo = min(0.0, (means - stds).min())
hi = (means + stds).max()
pad = (hi - lo) * 0.06

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=44,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=32,
    value_font_size=32,
    stroke_width=3,
    guide_stroke_color=GRID,
    guide_stroke_dasharray="4,6",
    opacity=1.0,
    opacity_hover=0.85,
)

chart = pygal.HorizontalBar(
    width=3200,
    height=1800,
    style=custom_style,
    title="bar-permutation-importance · python · pygal · anyplot.ai",
    x_title=IMPORTANCE,
    show_legend=False,
    print_values=False,
    show_y_guides=False,
    show_x_guides=True,
    range=(lo - pad if lo < 0 else -pad, hi + pad),
    margin_bottom=40,
    margin_left=420,
    margin_right=200,
    margin_top=40,
)
chart.x_labels = table[FEATURE].tolist()
chart.value_formatter = lambda x: f"{x:.2f}"

chart.add(
    IMPORTANCE,
    [
        {
            "value": mean,
            "color": color,
            "ci": {"low": mean - std, "high": mean + std},
            "label": f"{mean:.3f} ± {std:.3f}",
        }
        for mean, std, color in zip(means, stds, bar_colors, strict=True)
    ],
    formatter=lambda x: f"{x:.3f}",
)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
