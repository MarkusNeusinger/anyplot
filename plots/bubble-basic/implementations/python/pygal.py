"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: pygal 3.1.3 | Python 3.13.15
Quality: 86/100 | Created: 2026-09-27
"""

import os
import sys


# Remove the script's own directory from sys.path so `import pygal` resolves to the
# installed package rather than this file (which shares the package name).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
_r, _g, _b = int(INK_MUTED[1:3], 16), int(INK_MUTED[3:5], 16), int(INK_MUTED[5:7], 16)
GRID = f"rgba({_r}, {_g}, {_b}, 0.35)"  # lighter, theme-adaptive gridlines (pygal defaults to a hardcoded black)

# Data — Transit coverage vs congestion, bubble = vehicle registrations per 1,000 residents
np.random.seed(42)
n_cities = 50

# Uniform spread across the coverage range to avoid clustering
transit_coverage = np.concatenate(
    [np.random.uniform(10, 35, 15), np.random.uniform(35, 65, 20), np.random.uniform(65, 95, 15)]
)
np.random.shuffle(transit_coverage)

congestion_index = np.clip(85 - transit_coverage * 0.65 + np.random.normal(0, 6, n_cities), 15, 95)
vehicle_registrations = np.clip(200 + congestion_index * 4 + np.random.normal(0, 60, n_cities), 150, 700)

# Area-scaled bubble sizing via 7 tiers (pygal has no per-point size API).
# Quantile-based bin edges (rather than equal-width) keep tiers evenly
# populated, so no single tier absorbs most of the dense mid-chart cluster.
vr_min, vr_max = vehicle_registrations.min(), vehicle_registrations.max()

n_tiers = 7
bin_edges_vr = np.quantile(vehicle_registrations, np.linspace(0, 1, n_tiers + 1))
tier_bins = np.clip(np.digitize(vehicle_registrations, bin_edges_vr[1:-1]), 0, n_tiers - 1)

# sqrt of each tier's actual midpoint value (not tier index) for accurate area scaling
tier_mid_norm = [((bin_edges_vr[t] + bin_edges_vr[t + 1]) / 2 - vr_min) / (vr_max - vr_min) for t in range(n_tiers)]
tier_sizes = [int(20 + 100 * norm**0.5) for norm in tier_mid_norm]

# Imprint sequential colormap (imprint_seq): #009E73 (brand green) → #4467A3 (blue), equidistant stops
tier_colors = tuple(
    "#{:02X}{:02X}{:02X}".format(
        round(0x00 + (0x44 - 0x00) * i / (n_tiers - 1)),
        round(0x9E + (0x67 - 0x9E) * i / (n_tiers - 1)),
        round(0x73 + (0xA3 - 0x73) * i / (n_tiers - 1)),
    )
    for i in range(n_tiers)
)

# ANYPLOT_AMBER marks the focal city (6th color in the series cycle)
ANYPLOT_AMBER = "#DDCC77"
style_colors = tier_colors + (ANYPLOT_AMBER,)

# Tier labels serve as the size legend (vehicle-registration quantile ranges)
tier_labels = [f"{bin_edges_vr[t]:.0f}–{bin_edges_vr[t + 1]:.0f} vehicles/1,000" for t in range(n_tiers)]

# Focal city: highest congestion despite the data spread — visual anchor for data storytelling
focal_idx = int(np.argmax(congestion_index))
focal_tier = int(tier_bins[focal_idx])

# Group cities by vehicle-registration tier, excluding focal city
tier_data = {t: [] for t in range(n_tiers)}
for i in range(n_cities):
    if i == focal_idx:
        continue
    t = int(tier_bins[i])
    tier_data[t].append({"value": (round(float(transit_coverage[i]), 1), round(float(congestion_index[i]), 1))})

# `label` metadata (only set here, on the single focal point) drives pygal's
# `print_labels` static text overlay — the on-canvas annotation naming the
# hotspot's exact metrics. Every other point omits `label` so the overlay
# stays limited to this one bubble instead of cluttering all 50.
focal_point_data = [
    {
        "value": (round(float(transit_coverage[focal_idx]), 1), round(float(congestion_index[focal_idx]), 1)),
        "label": (
            f"★ Congestion Hotspot: {transit_coverage[focal_idx]:.0f}% coverage, "
            f"{congestion_index[focal_idx]:.0f} congestion index"
        ),
    }
]

# Style — theme-adaptive, anyplot sizing
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=style_colors,
    guide_stroke_color=GRID,
    major_guide_stroke_color=GRID,
    # `dot_opacity` (not `opacity`) governs the static fill/stroke alpha of XY
    # scatter dots — pygal's `.dot` CSS rule cascades after `.reactive`, so
    # `opacity` alone left bubbles fully solid in the previous pass despite the
    # spec's alpha-transparency requirement. `opacity_hover` still applies via
    # `.reactive.active` since `.dot` has no active-state fill-opacity rule.
    dot_opacity=0.58,
    opacity=0.70,
    opacity_hover=0.95,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    # `value_label_font_size` (not `value_font_size`) governs the `.text-overlay
    # text.label` CSS rule that print_labels renders into — a separate style
    # token pygal defaults to 10px regardless of the other font sizes above.
    # Left unset, the hotspot annotation fell back to that 10px default no
    # matter how large title/label/legend were configured.
    value_label_font_size=40,
    tooltip_font_size=36,
    title_font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
    label_font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
    major_label_font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
    legend_font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
    value_label_font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
)

# Plot
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="bubble-basic · python · pygal · anyplot.ai",
    x_title="Public Transit Coverage (%)",
    y_title="Traffic Congestion Index (0–100 scale)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=36,
    stroke=False,
    dots_size=20,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.0f}%",
    value_formatter=lambda x: f"{x:.0f}",
    margin_top=80,
    margin_bottom=200,
    margin_left=100,
    margin_right=80,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    print_values=False,
    print_labels=True,
    truncate_legend=30,
    spacing=30,
)

# Thin page-background "halo" ring around every bubble so overlapping dots
# keep a visible boundary in the dense low-coverage cluster, instead of
# melting into one blob under alpha blending. graph.css's default `.dot`
# rule ties stroke-opacity to dot_opacity and uses the fill color as the
# stroke, so the ring is invisible without an override. The override must
# repeat pygal's own `#chart-{uuid} .dot` id-scoped selector (only known
# once the chart object exists) to match its specificity, then rely on
# being appended last in the stylesheet to win the tie on source order.
#
# The `print_labels` annotation text renders into a `.text-overlay .label`
# node, but graph.css also emits a per-series `#chart-{uuid} .text-overlay
# .color-N text { fill: black }` rule (one per series color) that hardcodes
# black regardless of the Style object's foreground tokens. That per-series
# rule has 3 classes + 1 element, which beats a plain `.label` override's
# 2 classes + 0 elements on specificity alone — appending later in the
# stylesheet isn't enough to win. Matching `text.label` (element + class)
# brings the override to the same specificity as the color-N rule, so the
# existing "last in the stylesheet wins the tie" source-order rule (as used
# for the `.dot` halo override above) applies and it follows the theme.
chart.css = (
    "file://style.css",
    "file://graph.css",
    f"inline:#chart-{chart.uuid} .dot {{ stroke: {PAGE_BG}; stroke-width: 3px; stroke-opacity: 1; }}",
    f"inline:#chart-{chart.uuid} .text-overlay text.label {{ fill: {INK}; }}",
)

for t in range(n_tiers):
    chart.add(tier_labels[t], tier_data[t] if tier_data[t] else [], dots_size=tier_sizes[t])

# Focal city rendered last in ANYPLOT_AMBER — stands out as a visual anchor
chart.add("★ Congestion Hotspot", focal_point_data, dots_size=tier_sizes[focal_tier] + 8)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
