""" pyplots.ai
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

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#cccccc",
    colors=("#306998", "#E8775D", "#50A86E", "#D4A843", "#8B6BAE"),
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
    title="line-retention-cohort · pygal · pyplots.ai",
    x_title="Weeks Since Signup",
    y_title="Retained Users (%)",
    style=custom_style,
    show_dots=True,
    dots_size=6,
    stroke_style={"width": 5},
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    truncate_legend=-1,
    range=(0, 100),
    x_label_rotation=0,
)

chart.x_labels = [str(w) for w in weeks]

for cohort, params in cohorts.items():
    label = f"{cohort} (n={params['size']:,})"
    chart.add(label, retention_data[cohort])

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
