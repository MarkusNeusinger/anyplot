""" pyplots.ai
line-win-probability: Win Probability Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated NFL game: Eagles vs Cowboys
np.random.seed(42)

plays = 120

# Key waypoints: (play, win_probability)
waypoints = [
    (0, 0.50),
    (15, 0.38),  # DAL FG (3-0)
    (32, 0.62),  # PHI TD (7-3)
    (48, 0.35),  # DAL TD (10-7)
    (60, 0.40),  # Halftime drift
    (72, 0.65),  # PHI TD (14-10)
    (85, 0.74),  # PHI FG (17-10)
    (95, 0.45),  # DAL TD (17-17)
    (112, 0.88),  # PHI TD (24-17)
    (120, 0.97),  # Final
]

scoring_events = {
    15: "DAL FG\n3-0",
    32: "PHI TD\n7-3",
    48: "DAL TD\n10-7",
    72: "PHI TD\n14-10",
    85: "PHI FG\n17-10",
    95: "DAL TD\n17-17",
    112: "PHI TD\n24-17",
}

# Generate smooth win probability by interpolating between waypoints with noise
win_pct = np.zeros(plays + 1)
for i in range(len(waypoints) - 1):
    p1, v1 = waypoints[i]
    p2, v2 = waypoints[i + 1]
    n = p2 - p1
    t = np.linspace(0, 1, n, endpoint=False)
    # Smooth interpolation with slight S-curve
    interp = v1 + (v2 - v1) * (3 * t**2 - 2 * t**3)
    noise = np.random.normal(0, 0.012, n) * (1 - 0.7 * t)  # less noise near events
    win_pct[p1:p2] = np.clip(interp + noise, 0.02, 0.98)
win_pct[plays] = 0.97

# Snap scoring event values exactly
for play, _ in scoring_events.items():
    for p, v in waypoints:
        if p == play:
            win_pct[play] = v

# Convert to percentage
win_pct_list = [round(float(p) * 100, 1) for p in win_pct]

# Split fills: Eagles area above 50%, Cowboys area below 50%
# This avoids the muddy overlap from both series filling from 0
eagles_above = [max(pct, 50.0) for pct in win_pct_list]  # Clamp at 50 minimum
cowboys_below = [min(pct, 50.0) for pct in win_pct_list]  # Clamp at 50 maximum

# Custom style - Eagles green (#00843D) vs Cowboys blue (#003594) for high contrast
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e0e0e0",
    colors=("#003594", "#00843D", "#003594", "#00843D", "#333333", "#c0392b"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=34,
    major_label_font_size=42,
    value_font_size=28,
    legend_font_size=34,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=0.50,
    opacity_hover=0.65,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3,3",
    major_guide_stroke_color="#cccccc",
    major_guide_stroke_dasharray="6,3",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=28,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart
chart = pygal.Line(
    width=4800,
    height=2700,
    title="Eagles vs Cowboys (24-17) \u00b7 line-win-probability \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Game Progression",
    y_title="Win Probability (%)",
    style=custom_style,
    fill=False,
    show_dots=False,
    stroke_style={"width": 4},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    value_formatter=lambda x: f"{x:.0f}%",
    range=(0, 100),
    min_scale=5,
    max_scale=10,
    margin_bottom=100,
    margin_left=100,
    margin_right=60,
    margin_top=60,
    spacing=12,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    show_minor_x_labels=True,
    x_label_rotation=45,
)

# Series 1: Cowboys fill (constant 50% line, fills 0-50 in blue) — legend entry
chart.add("DAL Cowboys", [50.0] * len(win_pct_list), fill=True, show_dots=False, stroke_style={"width": 0})

# Series 2: Eagles fill (clamped above 50%, fills green above the 50% line) — legend entry
chart.add("PHI Eagles", eagles_above, fill=True, show_dots=False, stroke_style={"width": 0})

# Series 3: Cowboys advantage area (clamped below 50%) — hidden from legend
cowboys_below_data = [{"value": v, "label": ""} for v in cowboys_below]
chart.add(None, cowboys_below_data, fill=True, show_dots=False, stroke_style={"width": 0})

# Series 4: Win probability line (Eagles green, on top) — hidden from legend
chart.add(None, win_pct_list, fill=False, show_dots=False, stroke_style={"width": 5})

# Series 5: 50% baseline reference line
baseline = [50] * len(win_pct_list)
chart.add("50% Line", baseline, fill=False, show_dots=False, stroke_style={"width": 9, "dasharray": "20, 8"})

# Series 6: Scoring event markers with tooltip labels
event_series = [None] * len(win_pct_list)
for idx, label in scoring_events.items():
    event_series[idx] = {"value": win_pct_list[idx], "label": label}
chart.add("Scoring Events", event_series, fill=False, show_dots=True, dots_size=24, stroke=False)

# X-axis labels: quarter markers + scoring event annotations
label_map = {0: "Kickoff", 30: "Q2", 60: "Halftime", 90: "Q4", 120: "Final"}
# Add scoring event short labels to x-axis for visible annotations in PNG
scoring_labels = {
    15: "DAL FG 3-0",
    32: "PHI TD 7-3",
    48: "DAL TD 10-7",
    72: "PHI TD 14-10",
    85: "PHI FG 17-10",
    95: "DAL TD 17-17",
    112: "PHI TD 24-17",
}
label_map.update(scoring_labels)

chart.x_labels = [label_map.get(i, "") for i in range(plays + 1)]
chart.x_labels_major = list(label_map.values())
chart.truncate_label = -1

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
