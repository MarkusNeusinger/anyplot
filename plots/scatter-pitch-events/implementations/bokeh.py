""" pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, Label, NormalHead, Range1d
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
        angle = np.random.uniform(-np.pi / 2, np.pi / 2)
        dist = np.random.uniform(5, 40)
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

# Colorblind-safe palette: blue, red, gold, purple (maximally distinct)
event_colors = {"pass": "#306998", "shot": "#E63946", "tackle": "#E6A817", "interception": "#7B2D8E"}
event_markers = {"pass": "circle", "shot": "star", "tackle": "triangle", "interception": "diamond"}

# Visual hierarchy: shots are largest (focal point), others smaller
event_sizes = {"pass": 18, "shot": 30, "tackle": 20, "interception": 22}

# Plot
p = figure(
    width=4800,
    height=2700,
    title="scatter-pitch-events · bokeh · pyplots.ai",
    x_range=Range1d(-6, 111),
    y_range=Range1d(-16, 74),
    toolbar_location=None,
    match_aspect=True,
)

# Pitch background
p.rect(x=52.5, y=34, width=105, height=68, fill_color="#4a9e50", fill_alpha=0.15, line_color=None)

# Subtle pitch stripes for visual texture (alternating mow pattern)
for stripe_x in range(0, 105, 10):
    alpha = 0.04 if (stripe_x // 10) % 2 == 0 else 0.0
    p.rect(x=stripe_x + 5, y=34, width=10, height=68, fill_color="#2E7D32", fill_alpha=alpha, line_color=None)

# Danger zone gradient in attacking third — storytelling emphasis
p.rect(x=96, y=34, width=18, height=68, fill_color="#E63946", fill_alpha=0.06, line_color=None)
p.rect(x=100, y=34, width=10, height=68, fill_color="#E63946", fill_alpha=0.04, line_color=None)

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
p.line([-1.5, 0], [30.34, 30.34], line_color="#555555", line_width=6)
p.line([-1.5, 0], [37.66, 37.66], line_color="#555555", line_width=6)
p.line([-1.5, -1.5], [30.34, 37.66], line_color="#555555", line_width=6)
p.line([105, 106.5], [30.34, 30.34], line_color="#555555", line_width=6)
p.line([105, 106.5], [37.66, 37.66], line_color="#555555", line_width=6)
p.line([106.5, 106.5], [30.34, 37.66], line_color="#555555", line_width=6)

# Directional arrows for passes and shots
arrow_data = df[df["event_type"].isin(["pass", "shot"])]
for _, row in arrow_data.iterrows():
    color = event_colors[row["event_type"]]
    alpha = 0.55 if row["outcome"] == "successful" else 0.25
    lw = 2.5 if row["event_type"] == "shot" else 1.8
    head_size = 14 if row["event_type"] == "shot" else 10
    p.add_layout(
        Arrow(
            end=NormalHead(size=head_size, fill_color=color, fill_alpha=alpha, line_color=color, line_alpha=alpha),
            x_start=row["x"],
            y_start=row["y"],
            x_end=row["x_end"],
            y_end=row["y_end"],
            line_color=color,
            line_alpha=alpha,
            line_width=lw,
        )
    )

# Event markers — shots emphasized as focal point
for etype in ["pass", "tackle", "interception", "shot"]:
    for outcome in ["successful", "unsuccessful"]:
        mask = (df["event_type"] == etype) & (df["outcome"] == outcome)
        subset = df[mask]
        if len(subset) == 0:
            continue
        alpha = 0.9 if outcome == "successful" else 0.45
        fill = event_colors[etype] if outcome == "successful" else "white"
        line_w = 4 if etype == "shot" else 2.5
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
            line_width=line_w,
            line_alpha=0.95,
            legend_label=f"{etype.capitalize()} ({outcome})",
        )

# Storytelling annotation — highlight the danger zone
shot_data = df[df["event_type"] == "shot"]
n_shots = len(shot_data)
n_on_target = len(shot_data[shot_data["outcome"] == "successful"])
p.add_layout(
    Label(
        x=96,
        y=66,
        text=f"{n_shots} shots · {n_on_target} on target",
        text_font_size="22pt",
        text_color="#B71C1C",
        text_font_style="bold",
        text_alpha=0.8,
    )
)

# Legend — positioned below pitch
p.legend.location = "bottom_center"
p.legend.orientation = "horizontal"
p.legend.label_text_font_size = "22pt"
p.legend.label_text_color = "#333333"
p.legend.glyph_width = 32
p.legend.glyph_height = 32
p.legend.spacing = 30
p.legend.padding = 15
p.legend.background_fill_alpha = 0.92
p.legend.background_fill_color = "white"
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_width = 2
p.legend.ncols = 4
p.legend.click_policy = "hide"

# Style
p.title.text_font_size = "52pt"
p.title.text_color = "#222222"
p.title.text_font_style = "bold"

p.xaxis.axis_label = "Pitch Length (m)"
p.yaxis.axis_label = "Pitch Width (m)"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"
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

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FAFAFA"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-pitch-events · bokeh · pyplots.ai")
