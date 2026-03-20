""" pyplots.ai
line-win-probability: Win Probability Chart
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Span
from bokeh.plotting import figure


# Data - simulated NFL game: Eagles vs Cowboys
np.random.seed(42)

plays = np.arange(0, 121)
win_prob = np.full(121, 0.50)

# Simulate game flow with scoring events
events = {
    8: ("FG Eagles 3-0", 0.62),
    22: ("TD Cowboys 3-7", 0.38),
    35: ("TD Eagles 10-7", 0.58),
    48: ("FG Cowboys 10-10", 0.50),
    55: ("TD Eagles 17-10", 0.68),
    72: ("TD Cowboys 17-17", 0.48),
    85: ("FG Eagles 20-17", 0.63),
    95: ("INT Eagles", 0.72),
    105: ("TD Cowboys 20-24", 0.30),
    112: ("TD Eagles 27-24", 0.88),
    118: ("Turnover on downs", 0.97),
}

current_prob = 0.50
for i in range(1, 121):
    if i in events:
        current_prob = events[i][1]
    else:
        drift = np.random.normal(0, 0.015)
        current_prob = np.clip(current_prob + drift, 0.03, 0.97)
    win_prob[i] = current_prob

win_prob[120] = 1.0

# Smooth the line slightly with simple moving average
win_prob_smooth = np.convolve(win_prob, np.ones(3) / 3, mode="same")
win_prob_smooth[0] = 0.50
win_prob_smooth[120] = 1.0
for play in events:
    win_prob_smooth[play] = win_prob[play]

# Prepare fill data: split above/below 50%
upper = np.maximum(win_prob_smooth, 0.50)
lower = np.minimum(win_prob_smooth, 0.50)

source = ColumnDataSource(
    data={
        "play": plays,
        "win_prob": win_prob_smooth,
        "upper": upper,
        "lower": lower,
        "baseline": np.full(121, 0.50),
        "pct": win_prob_smooth * 100,
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Eagles vs Cowboys · line-win-probability · bokeh · pyplots.ai",
    x_axis_label="Play Number",
    y_axis_label="Eagles Win Probability (%)",
    y_range=(0, 1),
)

# Fill above 50% (home team - Eagles green)
eagles_fill = p.varea(x="play", y1="baseline", y2="upper", source=source, fill_color="#004C54", fill_alpha=0.3)

# Fill below 50% (away team - Cowboys blue)
cowboys_fill = p.varea(x="play", y1="lower", y2="baseline", source=source, fill_color="#869397", fill_alpha=0.35)

# Main probability line
prob_line = p.line(x="play", y="win_prob", source=source, line_color="#1a1a1a", line_width=5)

# Invisible scatter for hover targets
p.scatter(x="play", y="win_prob", source=source, size=18, fill_alpha=0, line_alpha=0)

# Hover tool
hover = HoverTool(tooltips=[("Play", "@play"), ("Win Prob", "@pct{0.0}%")], mode="vline")
p.add_tools(hover)

# 50% reference line
midline = Span(location=0.5, dimension="width", line_color="#888888", line_width=3, line_dash="dashed")
p.add_layout(midline)

# Quarter markers
quarter_plays = [30, 60, 90]
quarter_labels = ["Q2", "Q3", "Q4"]
for qp, ql in zip(quarter_plays, quarter_labels, strict=True):
    vline = Span(location=qp, dimension="height", line_color="#cccccc", line_width=2, line_dash="dotted")
    p.add_layout(vline)
    label = Label(
        x=qp, y=0.96, text=ql, text_font_size="26pt", text_color="#999999", text_align="center", x_offset=0, y_offset=10
    )
    p.add_layout(label)

# Legend for team colors
legend = Legend(
    items=[LegendItem(label="Eagles", renderers=[eagles_fill]), LegendItem(label="Cowboys", renderers=[cowboys_fill])],
    location="top_left",
    label_text_font_size="26pt",
    glyph_height=30,
    glyph_width=40,
    spacing=15,
    border_line_color=None,
    background_fill_alpha=0.7,
)
p.add_layout(legend)

# Annotate key scoring events with visual anchors
annotations = [
    (35, "TD Eagles 10-7", 12),
    (55, "TD Eagles 17-10", 12),
    (72, "TD Cowboys 17-17", -45),
    (105, "TD Cowboys 20-24", -45),
    (112, "TD Eagles 27-24", 12),
]

event_x = [a[0] for a in annotations]
event_y = [win_prob_smooth[a[0]] for a in annotations]
event_source = ColumnDataSource(data={"x": event_x, "y": event_y})
p.scatter(x="x", y="y", source=event_source, size=20, fill_color="#1a1a1a", line_color="white", line_width=3)

for play_num, text, y_off in annotations:
    label = Label(
        x=play_num,
        y=win_prob_smooth[play_num],
        text=text,
        text_font_size="22pt",
        text_color="#333333",
        text_font_style="bold",
        x_offset=8,
        y_offset=y_off,
    )
    p.add_layout(label)

# Final score annotation
score_label = Label(
    x=85,
    y=0.06,
    text="Final: Eagles 27 - Cowboys 24",
    text_font_size="34pt",
    text_color="#004C54",
    text_font_style="bold",
)
p.add_layout(score_label)

# Y-axis as percentage
p.yaxis.ticker = [0, 0.25, 0.50, 0.75, 1.0]
p.yaxis.major_label_overrides = {0: "0%", 0.25: "25%", 0.50: "50%", 0.75: "75%", 1.0: "100%"}

# Text sizing for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Clean frame - remove top/right spines for modern look
p.outline_line_color = None
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.toolbar_location = None

# Hide top and right axes (spines)
p.xaxis.axis_line_color = "#444444"
p.yaxis.axis_line_color = "#444444"
p.above = []
p.right = []

# Margins
p.min_border_left = 140
p.min_border_bottom = 120

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
