"""pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Legend, LegendItem, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
np.random.seed(42)
n_shots = 350

x = np.zeros(n_shots)
y = np.zeros(n_shots)
made = np.zeros(n_shots, dtype=bool)
shot_type = []

for i in range(n_shots):
    zone = np.random.choice(["paint", "midrange", "three", "corner3", "ft"], p=[0.25, 0.20, 0.30, 0.10, 0.15])
    if zone == "paint":
        x[i] = np.random.uniform(-8, 8)
        y[i] = np.random.uniform(0, 12)
        made[i] = np.random.random() < 0.55
        shot_type.append("2-pointer")
    elif zone == "midrange":
        x[i] = np.random.uniform(-16, 16)
        y[i] = np.random.uniform(5, 20)
        dist = np.sqrt(x[i] ** 2 + y[i] ** 2)
        while dist > 23.0 or dist < 5:
            x[i] = np.random.uniform(-16, 16)
            y[i] = np.random.uniform(5, 20)
            dist = np.sqrt(x[i] ** 2 + y[i] ** 2)
        made[i] = np.random.random() < 0.42
        shot_type.append("2-pointer")
    elif zone == "three":
        angle = np.random.uniform(0.25, np.pi - 0.25)
        r = np.random.uniform(24, 28)
        x[i] = r * np.cos(angle)
        y[i] = r * np.sin(angle)
        x[i] = np.clip(x[i], -24, 24)
        y[i] = np.clip(y[i], 10, 33)
        made[i] = np.random.random() < 0.36
        shot_type.append("3-pointer")
    elif zone == "corner3":
        side = np.random.choice([-1, 1])
        x[i] = side * np.random.uniform(21.5, 23)
        y[i] = np.random.uniform(0, 10)
        made[i] = np.random.random() < 0.39
        shot_type.append("3-pointer")
    else:
        x[i] = np.random.uniform(-0.8, 0.8)
        y[i] = np.random.uniform(14.5, 15.5)
        made[i] = np.random.random() < 0.78
        shot_type.append("free-throw")

shot_type = np.array(shot_type)

# Plot — 1:1 aspect ratio for undistorted court
p = figure(
    width=3600,
    height=3600,
    title="scatter-shot-chart · bokeh · pyplots.ai",
    x_range=Range1d(-27, 27),
    y_range=Range1d(-4, 36),
    toolbar_location=None,
    match_aspect=True,
)

# Court floor
p.rect(x=0, y=16, width=50, height=36, fill_color="#F5F0E8", line_color=None)

# Baseline and sidelines (half-court)
p.line([-25, 25], [0, 0], line_color="#888888", line_width=4)
p.line([-25, -25], [0, 35], line_color="#888888", line_width=3)
p.line([25, 25], [0, 35], line_color="#888888", line_width=3)

# Paint / key area (16 ft wide, 19 ft from baseline)
p.line([-8, -8, 8, 8], [0, 19, 19, 0], line_color="#888888", line_width=3)

# Free-throw circle (top half solid, bottom half dashed)
theta_top = np.linspace(0, np.pi, 100)
theta_bot = np.linspace(np.pi, 2 * np.pi, 100)
p.line(6 * np.cos(theta_top), 19 + 6 * np.sin(theta_top), line_color="#888888", line_width=3)
p.line(6 * np.cos(theta_bot), 19 + 6 * np.sin(theta_bot), line_color="#888888", line_width=2, line_dash="dashed")

# Restricted area arc (4 ft radius from basket center)
theta_ra = np.linspace(0, np.pi, 100)
p.line(4 * np.cos(theta_ra), 4 * np.sin(theta_ra), line_color="#888888", line_width=2)

# Three-point arc (23.75 ft at top, 22 ft corners)
theta_3pt = np.linspace(np.arccos(22.0 / 23.75), np.pi - np.arccos(22.0 / 23.75), 200)
p.line(23.75 * np.cos(theta_3pt), 23.75 * np.sin(theta_3pt), line_color="#888888", line_width=3)

# Corner three-point lines (22 ft from basket, straight down to baseline)
corner_y = 23.75 * np.sin(np.arccos(22.0 / 23.75))
p.line([-22, -22], [0, corner_y], line_color="#888888", line_width=3)
p.line([22, 22], [0, corner_y], line_color="#888888", line_width=3)

# Basket (hoop at center of rim, ~1.5 ft from backboard)
hoop_theta = np.linspace(0, 2 * np.pi, 50)
p.line(0.75 * np.cos(hoop_theta), 0.75 * np.sin(hoop_theta) + 1.5, line_color="#C44E2B", line_width=5)

# Backboard
p.line([-3, 3], [0, 0], line_color="#555555", line_width=6)

# Shot markers — made (green circles) and missed (red X)
made_mask = made
missed_mask = ~made

source_made = ColumnDataSource(data={"x": x[made_mask], "y": y[made_mask]})
source_missed = ColumnDataSource(data={"x": x[missed_mask], "y": y[missed_mask]})

r_made = p.scatter(
    x="x",
    y="y",
    source=source_made,
    size=20,
    fill_color="#2E8B57",
    fill_alpha=0.8,
    line_color="white",
    line_width=1.5,
    marker="circle",
)

r_missed = p.scatter(
    x="x",
    y="y",
    source=source_missed,
    size=18,
    fill_color=None,
    fill_alpha=0,
    line_color="#D94F4F",
    line_width=3.5,
    marker="x",
)

# Legend
n_made = int(np.sum(made))
n_missed = int(np.sum(~made))
legend = Legend(
    items=[
        LegendItem(label=f"Made ({n_made})", renderers=[r_made]),
        LegendItem(label=f"Missed ({n_missed})", renderers=[r_missed]),
    ],
    location="top_center",
    orientation="horizontal",
)

p.add_layout(legend, "above")
p.legend.label_text_font_size = "28pt"
p.legend.label_text_color = "#333333"
p.legend.glyph_width = 40
p.legend.glyph_height = 40
p.legend.spacing = 50
p.legend.padding = 20
p.legend.background_fill_alpha = 0.0
p.legend.border_line_color = None

# FG% summary
fg_pct = n_made / n_shots * 100
p.add_layout(
    Label(
        x=0,
        y=33.5,
        text=f"FG: {fg_pct:.1f}%  ·  {n_shots} attempts",
        text_font_size="26pt",
        text_color="#666666",
        text_align="center",
        text_font_style="bold",
    )
)

# Style
p.title.text_font_size = "40pt"
p.title.text_color = "#222222"
p.title.text_font_style = "bold"
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.background_fill_color = "#F5F0E8"
p.border_fill_color = "#FAFAFA"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-shot-chart · bokeh · pyplots.ai")
