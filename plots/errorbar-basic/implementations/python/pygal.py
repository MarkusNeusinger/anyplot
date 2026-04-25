""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-25
"""

import os

import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1 — primary data color

# Data — dose-response study: vehicle control + escalating doses (mg/kg)
categories = ["Vehicle", "1 mg/kg", "3 mg/kg", "10 mg/kg", "30 mg/kg", "100 mg/kg"]
means = [25.3, 28.4, 33.1, 38.7, 47.5, 42.0]
# Asymmetric errors: 10 and 30 mg/kg show notable lower-tail variability
err_lower = [2.1, 2.5, 3.0, 6.2, 4.8, 3.4]
err_upper = [2.1, 2.5, 3.0, 2.8, 2.2, 3.4]

n = len(categories)
baseline = means[0]  # Vehicle/control mean — visual reference for treatment effects

# Style — first series (baseline reference) uses muted ink, all data series use brand green
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(INK_MUTED,) + (BRAND,) * 64,
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=40,
    legend_font_size=36,
    value_font_size=28,
    tooltip_font_size=32,
    stroke_width=6,
    opacity=1.0,
    opacity_hover=0.85,
)

# Y-axis zoomed to the data band with breathing room above and below
data_min = min(m - e for m, e in zip(means, err_lower, strict=True))
data_max = max(m + e for m, e in zip(means, err_upper, strict=True))
pad = (data_max - data_min) * 0.15
y_min = max(0.0, data_min - pad)
y_max = data_max + pad

# x positions shifted to 1..n so pygal's implicit x=0 line stays off-canvas
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    dots_size=24,
    title="errorbar-basic · pygal · anyplot.ai",
    x_title="Dose",
    y_title="Response Value (units)",
    show_legend=True,
    legend_at_bottom=True,
    range=(y_min, y_max),
    xrange=(0.5, n + 0.5),
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    margin=40,
    margin_right=80,
)

chart.x_labels = [{"label": categories[i], "value": i + 1} for i in range(n)]
chart.x_labels_major = [{"label": categories[i], "value": i + 1} for i in range(n)]

# Vehicle baseline reference line — visual hierarchy anchor at control mean
chart.add(
    "Vehicle baseline",
    [(0.5, baseline), (n + 0.5, baseline)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "18, 14"},
)

cap_width = 0.16  # Width of error bar caps in x-axis units

# Mean points with rich tooltip labels (pygal interactive feature)
mean_points = [
    {"value": (i + 1, means[i]), "label": f"{categories[i]}: {means[i]:.1f} (-{err_lower[i]:.1f}/+{err_upper[i]:.1f})"}
    for i in range(n)
]
chart.add("Mean ± error", mean_points, stroke=False, dots_size=28)

# Error bars: separate series per segment for clean line breaks (no legend entry)
for i in range(n):
    x = i + 1
    low = means[i] - err_lower[i]
    high = means[i] + err_upper[i]

    chart.add(None, [(x, low), (x, high)], stroke=True, show_dots=False)
    chart.add(None, [(x - cap_width, low), (x + cap_width, low)], stroke=True, show_dots=False)
    chart.add(None, [(x - cap_width, high), (x + cap_width, high)], stroke=True, show_dots=False)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
