"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, NormalHead, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
np.random.seed(42)
n_events = 120

event_types = np.random.choice(["pass", "shot", "tackle", "interception"], size=n_events, p=[0.45, 0.15, 0.22, 0.18])

x_start = np.zeros(n_events)
y_start = np.zeros(n_events)
x_end = np.zeros(n_events)
y_end = np.zeros(n_events)
outcomes = []

for i, etype in enumerate(event_types):
    if etype == "pass":
        x_start[i] = np.random.uniform(10, 90)
        y_start[i] = np.random.uniform(5, 63)
        angle = np.random.uniform(-np.pi / 3, np.pi / 3)
        dist = np.random.uniform(5, 30)
        x_end[i] = np.clip(x_start[i] + dist * np.cos(angle), 0, 105)
        y_end[i] = np.clip(y_start[i] + dist * np.sin(angle), 0, 68)
        outcomes.append(np.random.choice(["successful", "unsuccessful"], p=[0.78, 0.22]))
    elif etype == "shot":
        x_start[i] = np.random.uniform(70, 100)
        y_start[i] = np.random.uniform(15, 53)
        x_end[i] = 105
        y_end[i] = np.random.uniform(28, 40)
        outcomes.append(np.random.choice(["successful", "unsuccessful"], p=[0.30, 0.70]))
    elif etype == "tackle":
        x_start[i] = np.random.uniform(15, 75)
        y_start[i] = np.random.uniform(5, 63)
        x_end[i] = x_start[i]
        y_end[i] = y_start[i]
        outcomes.append(np.random.choice(["successful", "unsuccessful"], p=[0.65, 0.35]))
    else:
        x_start[i] = np.random.uniform(20, 80)
        y_start[i] = np.random.uniform(5, 63)
        x_end[i] = x_start[i]
        y_end[i] = y_start[i]
        outcomes.append(np.random.choice(["successful", "unsuccessful"], p=[0.72, 0.28]))

outcomes = np.array(outcomes)

df = pd.DataFrame(
    {"x": x_start, "y": y_start, "x_end": x_end, "y_end": y_end, "event_type": event_types, "outcome": outcomes}
)

# Color and marker mapping
event_colors = {"pass": "#306998", "shot": "#E63946", "tackle": "#2A9D8F", "interception": "#E9C46A"}
event_markers = {"pass": "circle", "shot": "star", "tackle": "triangle", "interception": "diamond"}
event_sizes = {"pass": 20, "shot": 28, "tackle": 22, "interception": 20}

# Plot
pitch_margin = 5
p = figure(
    width=4800,
    height=2700,
    title="scatter-pitch-events · bokeh · pyplots.ai",
    x_range=Range1d(-pitch_margin, 105 + pitch_margin),
    y_range=Range1d(-pitch_margin - 12, 68 + pitch_margin),
    toolbar_location=None,
    match_aspect=True,
)

# Pitch background
p.rect(x=52.5, y=34, width=105, height=68, fill_color="#3a8c3f", fill_alpha=0.18, line_color="#2E7D32", line_width=4)

# Pitch zone shading — attacking third highlighted
p.rect(x=87.5, y=34, width=35, height=68, fill_color="#E63946", fill_alpha=0.04, line_color=None)
p.rect(x=17.5, y=34, width=35, height=68, fill_color="#306998", fill_alpha=0.04, line_color=None)

# Pitch outline
p.line([0, 105, 105, 0, 0], [0, 0, 68, 68, 0], line_color="#2E7D32", line_width=4)

# Halfway line
p.line([52.5, 52.5], [0, 68], line_color="#2E7D32", line_width=3)

# Center circle
theta = np.linspace(0, 2 * np.pi, 100)
p.line(52.5 + 9.15 * np.cos(theta), 34 + 9.15 * np.sin(theta), line_color="#2E7D32", line_width=3)
p.scatter([52.5], [34], size=10, color="#2E7D32")

# Left penalty area
p.line([0, 16.5, 16.5, 0], [13.85, 13.85, 54.15, 54.15], line_color="#2E7D32", line_width=3)

# Right penalty area
p.line([105, 88.5, 88.5, 105], [13.85, 13.85, 54.15, 54.15], line_color="#2E7D32", line_width=3)

# Left goal area
p.line([0, 5.5, 5.5, 0], [24.85, 24.85, 43.15, 43.15], line_color="#2E7D32", line_width=3)

# Right goal area
p.line([105, 99.5, 99.5, 105], [24.85, 24.85, 43.15, 43.15], line_color="#2E7D32", line_width=3)

# Penalty spots
p.scatter([11, 94], [34, 34], size=8, color="#2E7D32")

# Penalty arcs
arc_theta = np.linspace(-0.93, 0.93, 50)
p.line(11 + 9.15 * np.cos(arc_theta), 34 + 9.15 * np.sin(arc_theta), line_color="#2E7D32", line_width=3)
p.line(94 - 9.15 * np.cos(arc_theta), 34 + 9.15 * np.sin(arc_theta), line_color="#2E7D32", line_width=3)

# Corner arcs
for cx, cy, a0, a1 in [
    (0, 0, 0, np.pi / 2),
    (105, 0, np.pi / 2, np.pi),
    (105, 68, np.pi, 3 * np.pi / 2),
    (0, 68, 3 * np.pi / 2, 2 * np.pi),
]:
    ca = np.linspace(a0, a1, 25)
    p.line(cx + 1 * np.cos(ca), cy + 1 * np.sin(ca), line_color="#2E7D32", line_width=3)

# Goal posts
p.line([-1, 0], [30.34, 30.34], line_color="#444444", line_width=5)
p.line([-1, 0], [37.66, 37.66], line_color="#444444", line_width=5)
p.line([-1, -1], [30.34, 37.66], line_color="#444444", line_width=5)
p.line([105, 106], [30.34, 30.34], line_color="#444444", line_width=5)
p.line([105, 106], [37.66, 37.66], line_color="#444444", line_width=5)
p.line([106, 106], [30.34, 37.66], line_color="#444444", line_width=5)

# Directional arrows for passes and shots
arrow_df = df[df["event_type"].isin(["pass", "shot"])]
for etype, grp in arrow_df.groupby("event_type"):
    color = event_colors[etype]
    for outcome, sub in grp.groupby("outcome"):
        alpha = 0.7 if outcome == "successful" else 0.35
        for xs, ys, xe, ye in zip(sub["x"], sub["y"], sub["x_end"], sub["y_end"], strict=False):
            p.add_layout(
                Arrow(
                    end=NormalHead(size=12, fill_color=color, fill_alpha=alpha, line_color=color, line_alpha=alpha),
                    x_start=xs,
                    y_start=ys,
                    x_end=xe,
                    y_end=ye,
                    line_color=color,
                    line_alpha=alpha,
                    line_width=2,
                )
            )

# Event markers with size variation for visual hierarchy
for etype in ["pass", "shot", "tackle", "interception"]:
    for outcome in ["successful", "unsuccessful"]:
        mask = (df["event_type"] == etype) & (df["outcome"] == outcome)
        subset = df[mask]
        if len(subset) == 0:
            continue
        alpha = 0.9 if outcome == "successful" else 0.5
        fill = event_colors[etype] if outcome == "successful" else "white"
        source = ColumnDataSource(data={"x": subset["x"].values, "y": subset["y"].values})
        p.scatter(
            x="x",
            y="y",
            source=source,
            marker=event_markers[etype],
            size=event_sizes[etype],
            fill_color=fill,
            fill_alpha=alpha,
            line_color=event_colors[etype],
            line_width=3,
            line_alpha=0.9,
            legend_label=f"{etype.capitalize()} ({outcome})",
        )

# Legend — positioned below pitch to avoid overlap
p.legend.location = "bottom_center"
p.legend.orientation = "horizontal"
p.legend.label_text_font_size = "24pt"
p.legend.glyph_width = 35
p.legend.glyph_height = 35
p.legend.spacing = 20
p.legend.padding = 12
p.legend.background_fill_alpha = 0.9
p.legend.background_fill_color = "white"
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_width = 2
p.legend.ncols = 4

# Style
p.title.text_font_size = "60pt"
p.title.text_color = "#333333"

p.xaxis.axis_label = "Pitch Length (m)"
p.yaxis.axis_label = "Pitch Width (m)"
p.xaxis.axis_label_text_font_size = "40pt"
p.yaxis.axis_label_text_font_size = "40pt"
p.xaxis.major_label_text_font_size = "30pt"
p.yaxis.major_label_text_font_size = "30pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.grid.grid_line_color = None

p.background_fill_color = "white"
p.border_fill_color = "white"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-pitch-events · bokeh · pyplots.ai")
