"""pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-16
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

# Style - reference line color first, then cohort colors fading from muted to vivid
colors_with_opacity = (
    "rgba(180, 60, 60, 0.6)",
    "rgba(48, 105, 152, 0.45)",
    "rgba(232, 119, 93, 0.55)",
    "rgba(80, 168, 110, 0.70)",
    "rgba(212, 168, 67, 0.85)",
    "rgba(139, 107, 174, 1.0)",
)

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#cccccc",
    colors=colors_with_opacity,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=40,
    value_font_size=36,
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
    stroke_style={"width": 3},
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    truncate_legend=-1,
    range=(0, 105),
    x_label_rotation=0,
    value_formatter=lambda x: f"{x:.0f}%" if x is not None else "",
    tooltip_fancy_mode=True,
    interpolate="cubic",
)

chart.x_labels = [str(w) for w in weeks]

# Add reference threshold line at 20% retention
chart.add(
    "20% Retention Threshold",
    [20.0] * len(weeks),
    stroke_style={"width": 2, "dasharray": "12, 8"},
    show_dots=False,
    dots_size=0,
)

# Add cohorts with increasing stroke width for newer cohorts
stroke_widths = [2, 3, 4, 5, 7]
dot_sizes = [4, 5, 5, 6, 8]
cohort_list = list(cohorts.items())

for i, (cohort, params) in enumerate(cohort_list):
    label = f"{cohort} (n={params['size']:,})"
    chart.add(
        label,
        [{"value": v, "label": f"Week {w}: {v:.1f}% retained"} for w, v in zip(weeks, retention_data[cohort], strict=True)],
        stroke_style={"width": stroke_widths[i]},
        dots_size=dot_sizes[i],
    )

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
