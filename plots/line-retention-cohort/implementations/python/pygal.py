""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: pygal 3.1.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-16
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Monthly signup cohorts tracked weekly for 12 weeks
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.18},
    "Feb 2025": {"size": 1102, "decay": 0.16},
    "Mar 2025": {"size": 1380, "decay": 0.14},
    "Apr 2025": {"size": 1467, "decay": 0.12},
    "May 2025": {"size": 1590, "decay": 0.11},
}

weeks = list(range(13))
retention_data = {}
for cohort, params in cohorts.items():
    retention = [100.0]
    for week in range(1, 13):
        noise = np.random.normal(0, 1.5)
        prev = retention[-1]
        drop = prev * params["decay"] * (1 / (1 + 0.1 * week)) + noise
        retention.append(max(round(prev - max(drop, 0.5), 1), 5.0))
    retention_data[cohort] = retention

# Style - bold palette with strong contrast, threshold line first
colors_with_opacity = (
    "#B03030",
    "rgba(48, 105, 152, 0.80)",
    "rgba(215, 100, 45, 0.85)",
    "rgba(45, 155, 90, 0.88)",
    "rgba(200, 155, 30, 0.92)",
    "rgba(115, 70, 170, 1.0)",
)

custom_style = Style(
    background="#f7f7f7",
    plot_background="#fdfdfd",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    colors=colors_with_opacity,
    title_font_size=74,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=46,
    value_font_size=36,
    opacity=".95",
    opacity_hover="1",
    transition="200ms ease-in",
    font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    title_font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    legend_font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    label_font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    major_label_font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    value_font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    stroke_width=5,
)

# Plot
chart = pygal.Line(
    width=4800,
    height=2700,
    title="line-retention-cohort \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Weeks Since Signup",
    y_title="Retained Users (%)",
    style=custom_style,
    show_dots=True,
    dots_size=6,
    stroke_style={"width": 4},
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=28,
    truncate_legend=-1,
    range=(0, 102),
    x_label_rotation=0,
    value_formatter=lambda x: f"{x:.0f}%" if x is not None else "",
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    interpolate="cubic",
    show_minor_x_labels=False,
    y_labels=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    margin_top=50,
    margin_bottom=50,
    margin_left=30,
    margin_right=30,
    spacing=25,
    print_values=False,
    dynamic_print_values=True,
    no_data_text="No data available",
)

chart.x_labels = [str(w) for w in weeks]
chart.x_labels_major = ["0", "3", "6", "9", "12"]

# Add reference threshold line at 20% retention
chart.add(
    "\u2500\u2500 20% Retention Threshold",
    [{"value": 20.0, "label": "Target: 20% retention benchmark"}] * len(weeks),
    stroke_style={"width": 6, "dasharray": "24, 14", "linecap": "round"},
    show_dots=False,
    dots_size=0,
    allow_interruptions=False,
)

# Add cohorts with increasing stroke width and dot size for newer cohorts
stroke_widths = [4, 4.5, 5.5, 6.5, 8]
dot_sizes = [5, 6, 7, 8, 10]
cohort_list = list(cohorts.items())

for i, (cohort, params) in enumerate(cohort_list):
    label = f"{cohort} (n={params['size']:,})"
    values = retention_data[cohort]
    chart.add(
        label,
        [
            {"value": v, "label": f"Week {w}: {v:.1f}% retained ({int(params['size'] * v / 100):,} users)"}
            for w, v in zip(weeks, values, strict=True)
        ],
        stroke_style={"width": stroke_widths[i], "linecap": "round", "linejoin": "round"},
        dots_size=dot_sizes[i],
        allow_interruptions=False,
    )

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
