""" pyplots.ai
line-win-probability: Win Probability Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated NFL game: Eagles vs Cowboys
np.random.seed(42)

plays = 120

# Start at 50%, simulate momentum shifts with key scoring events
win_prob = [0.50]
scoring_events = {}

# Q1: Cowboys FG at play 15
for _ in range(1, 16):
    win_prob.append(win_prob[-1] + np.random.normal(-0.002, 0.015))
win_prob[15] = 0.38
scoring_events[15] = "DAL FG (3-0)"

# Q1-Q2: Eagles TD at play 32
for _ in range(16, 33):
    win_prob.append(win_prob[-1] + np.random.normal(0.003, 0.012))
win_prob[32] = 0.62
scoring_events[32] = "PHI TD (7-3)"

# Q2: Cowboys TD at play 48
for _ in range(33, 49):
    win_prob.append(win_prob[-1] + np.random.normal(-0.004, 0.015))
win_prob[48] = 0.35
scoring_events[48] = "DAL TD (10-7)"

# Halftime drifts
for _ in range(49, 61):
    win_prob.append(win_prob[-1] + np.random.normal(0.001, 0.010))

# Q3: Eagles TD at play 72
for _ in range(61, 73):
    win_prob.append(win_prob[-1] + np.random.normal(0.005, 0.012))
win_prob[72] = 0.65
scoring_events[72] = "PHI TD (14-10)"

# Q3: Eagles FG at play 85
for _ in range(73, 86):
    win_prob.append(win_prob[-1] + np.random.normal(0.002, 0.010))
win_prob[85] = 0.74
scoring_events[85] = "PHI FG (17-10)"

# Q4: Cowboys TD at play 95 - ties the game
for _ in range(86, 96):
    win_prob.append(win_prob[-1] + np.random.normal(-0.006, 0.015))
win_prob[95] = 0.45
scoring_events[95] = "DAL TD (17-17)"

# Q4: Eagles game-winning TD at play 112
for _ in range(96, 113):
    win_prob.append(win_prob[-1] + np.random.normal(0.005, 0.018))
win_prob[112] = 0.88
scoring_events[112] = "PHI TD (24-17)"

# Final plays coast to end
for _ in range(113, plays + 1):
    win_prob.append(win_prob[-1] + np.random.normal(0.008, 0.005))
win_prob[plays] = 0.97

# Clamp values to [0.02, 0.98] except final
win_prob = [max(0.02, min(0.98, p)) for p in win_prob]
win_prob[plays] = 0.97

# Convert to percentages
win_pct = [p * 100 for p in win_prob]

# Two-color fill data: split at 50% baseline
# Cowboys fill: constant 50 (renders first, fills 0-50 in Cowboys blue)
cowboys_fill = [50.0] * len(win_pct)
# Eagles fill: actual win probability (renders second, fills 0-pct in Eagles teal)
# When pct > 50: Eagles teal covers Cowboys blue, teal visible from 50 to pct
# When pct < 50: Cowboys blue visible from pct to 50 (showing Cowboys momentum)
eagles_fill = [round(pct, 1) for pct in win_pct]

# Custom style - Eagles teal (#004C54) vs Cowboys navy (#003594)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e0e0e0",
    colors=("#003594", "#004C54", "#1a1a1a", "#d4380d"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=42,
    value_font_size=32,
    legend_font_size=34,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=0.55,
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
    interpolate="cubic",
    interpolation_precision=200,
    min_scale=5,
    max_scale=10,
    margin_bottom=120,
    margin_left=100,
    margin_right=60,
    margin_top=60,
    spacing=12,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    show_minor_x_labels=False,
)

# Series 1: Cowboys fill area (constant 50%, fills 0-50 in Cowboys blue)
chart.add("DAL Cowboys", cowboys_fill, fill=True, show_dots=False, stroke_style={"width": 0})

# Series 2: Eagles win probability (fills 0-pct in Eagles teal, overlaying Cowboys)
eagles_data = []
for i, pct in enumerate(win_pct):
    label = scoring_events.get(i, None)
    if label:
        eagles_data.append({"value": round(pct, 1), "label": label})
    else:
        eagles_data.append(round(pct, 1))
chart.add("PHI Eagles", eagles_data, fill=True, stroke_style={"width": 5})

# Series 3: 50% baseline reference line (prominent, dark, dashed)
baseline = [50] * len(win_pct)
chart.add("50% Baseline", baseline, fill=False, show_dots=False, stroke_style={"width": 6, "dasharray": "20, 12"})

# Series 4: Scoring event markers with labels
event_series = [None] * len(win_pct)
for idx, label in scoring_events.items():
    event_series[idx] = {"value": round(win_pct[idx], 1), "label": label}
chart.add("Key Plays", event_series, fill=False, show_dots=True, dots_size=22, stroke=False)

# X-axis labels: quarter markers + scoring event annotations
x_labels = []
quarter_plays = {0: "Kickoff", 30: "Q2", 60: "Halftime", 90: "Q4", 120: "Final"}
for i in range(plays + 1):
    if i in quarter_plays:
        x_labels.append(quarter_plays[i])
    elif i in scoring_events:
        x_labels.append(scoring_events[i])
    else:
        x_labels.append("")
chart.x_labels = x_labels
chart.x_labels_major = [
    "Kickoff",
    "Q2",
    "Halftime",
    "Q4",
    "Final",
    "DAL FG (3-0)",
    "PHI TD (7-3)",
    "DAL TD (10-7)",
    "PHI TD (14-10)",
    "PHI FG (17-10)",
    "DAL TD (17-17)",
    "PHI TD (24-17)",
]
chart.truncate_label = -1
chart.x_label_rotation = 35

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
