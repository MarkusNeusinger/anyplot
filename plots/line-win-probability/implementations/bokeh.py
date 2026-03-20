""" pyplots.ai
line-win-probability: Win Probability Chart
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import (
    Band,
    ColumnDataSource,
    CustomJS,
    HoverTool,
    Label,
    Legend,
    LegendItem,
    NumeralTickFormatter,
    Span,
)
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
    title="line-win-probability · bokeh · pyplots.ai",
    x_axis_label="Play Number",
    y_axis_label="Win Probability (%)",
    y_range=(-0.02, 1.02),
    x_range=(-3, 126),
)

# Fill above 50% (home team - Eagles teal)
eagles_fill = p.varea(x="play", y1="baseline", y2="upper", source=source, fill_color="#004C54", fill_alpha=0.25)

# Fill below 50% (away team - Cowboys silver)
cowboys_fill = p.varea(x="play", y1="lower", y2="baseline", source=source, fill_color="#869397", fill_alpha=0.3)

# Confidence band around probability line
band_upper = np.clip(win_prob_smooth + 0.04, 0, 1)
band_lower = np.clip(win_prob_smooth - 0.04, 0, 1)
band_source = ColumnDataSource(data={"play": plays, "upper": band_upper, "lower": band_lower})
band = Band(
    base="play",
    upper="upper",
    lower="lower",
    source=band_source,
    fill_color="#1a1a1a",
    fill_alpha=0.06,
    line_color=None,
)
p.add_layout(band)

# Main probability line with gradient effect via overlapping lines
p.line(x="play", y="win_prob", source=source, line_color="#3a3a3a", line_width=8, line_alpha=0.3)
prob_line = p.line(x="play", y="win_prob", source=source, line_color="#1a1a1a", line_width=4)

# Invisible scatter for hover targets
hover_scatter = p.scatter(x="play", y="win_prob", source=source, size=22, fill_alpha=0, line_alpha=0)

# Hover tool with rich HTML tooltips (Bokeh-distinctive)
hover = HoverTool(
    renderers=[hover_scatter],
    tooltips="""
    <div style="background:#2a2a2a; padding:12px 16px; border-radius:8px; color:white; font-size:16px; line-height:1.6;">
        <span style="font-weight:bold; font-size:18px;">Play @play</span><br>
        <span style="color:#66ccbb;">Win Prob: @pct{0.1}%</span>
    </div>
    """,
    mode="vline",
)
p.add_tools(hover)

# CustomJS callback for crosshair effect on hover (Bokeh-distinctive interactivity)
crosshair_source = ColumnDataSource(data={"x": [0], "y": [0]})
crosshair_v = Span(
    location=0, dimension="height", line_color="#004C54", line_width=2, line_alpha=0.4, line_dash="solid"
)
p.add_layout(crosshair_v)
callback = CustomJS(
    args={"span": crosshair_v},
    code="""
    const geometry = cb_data.geometry;
    span.location = geometry.x;
    """,
)
hover.callback = callback

# 50% reference line
midline = Span(location=0.5, dimension="width", line_color="#999999", line_width=2, line_dash=[12, 6])
p.add_layout(midline)

# Team name labels at 50% line edges
eagles_team_label = Label(
    x=2, y=0.52, text="EAGLES", text_font_size="20pt", text_color="#004C54", text_font_style="bold", text_alpha=0.5
)
cowboys_team_label = Label(
    x=2, y=0.44, text="COWBOYS", text_font_size="20pt", text_color="#869397", text_font_style="bold", text_alpha=0.5
)
p.add_layout(eagles_team_label)
p.add_layout(cowboys_team_label)

# Quarter markers with subtle background bands
quarter_boundaries = [(0, 30), (30, 60), (60, 90), (90, 120)]
quarter_names = ["Q1", "Q2", "Q3", "Q4"]
for idx, ((q_start, q_end), q_name) in enumerate(zip(quarter_boundaries, quarter_names, strict=True)):
    if idx % 2 == 1:
        q_band_source = ColumnDataSource(data={"x": [q_start, q_end], "upper": [1.02, 1.02], "lower": [-0.02, -0.02]})
        q_band = Band(
            base="x",
            upper="upper",
            lower="lower",
            source=q_band_source,
            fill_color="#000000",
            fill_alpha=0.02,
            line_color=None,
        )
        p.add_layout(q_band)
    if q_start > 0:
        vline = Span(location=q_start, dimension="height", line_color="#bbbbbb", line_width=2, line_dash="dotted")
        p.add_layout(vline)
    label = Label(
        x=(q_start + q_end) / 2,
        y=0.97,
        text=q_name,
        text_font_size="22pt",
        text_color="#aaaaaa",
        text_align="center",
        text_font_style="bold",
    )
    p.add_layout(label)

# Legend for team colors
legend = Legend(
    items=[LegendItem(label="Eagles", renderers=[eagles_fill]), LegendItem(label="Cowboys", renderers=[cowboys_fill])],
    location="top_left",
    label_text_font_size="24pt",
    glyph_height=28,
    glyph_width=38,
    spacing=12,
    border_line_color=None,
    background_fill_alpha=0.6,
    background_fill_color="#f8f8f8",
    padding=20,
)
p.add_layout(legend)

# Annotate key scoring events - spread out to avoid crowding
annotations = [
    (35, "TD Eagles 10-7", 14, -20),
    (55, "TD Eagles 17-10", 14, 0),
    (72, "TD Cowboys 17-17", -48, 0),
    (105, "TD Cowboys 20-24", -48, 15),
    (112, "TD Eagles 27-24", 14, -30),
]

event_x = [a[0] for a in annotations]
event_y = [win_prob_smooth[a[0]] for a in annotations]
event_source = ColumnDataSource(data={"x": event_x, "y": event_y})
p.scatter(x="x", y="y", source=event_source, size=18, fill_color="#004C54", line_color="white", line_width=3, alpha=0.9)

for play_num, text, y_off, x_off in annotations:
    label = Label(
        x=play_num,
        y=win_prob_smooth[play_num],
        text=text,
        text_font_size="20pt",
        text_color="#2a2a2a",
        text_font_style="bold",
        x_offset=x_off,
        y_offset=y_off,
        background_fill_color="white",
        background_fill_alpha=0.75,
    )
    p.add_layout(label)

# Final score annotation with styled box
score_label = Label(
    x=78,
    y=0.08,
    text="Final: Eagles 27 - Cowboys 24",
    text_font_size="32pt",
    text_color="#004C54",
    text_font_style="bold",
    background_fill_color="white",
    background_fill_alpha=0.8,
)
p.add_layout(score_label)

# Y-axis as percentage using NumeralTickFormatter
p.yaxis.ticker = [0, 0.25, 0.50, 0.75, 1.0]
p.yaxis.formatter = NumeralTickFormatter(format="0%")

# Text sizing for 4800x2700 canvas
p.title.text_font_size = "40pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "30pt"
p.yaxis.axis_label_text_font_size = "30pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_text_color = "#555555"
p.yaxis.axis_label_text_color = "#555555"
p.xaxis.major_label_text_color = "#666666"
p.yaxis.major_label_text_color = "#666666"

# Grid styling - subtle horizontal emphasis
p.xgrid.grid_line_alpha = 0.08
p.ygrid.grid_line_alpha = 0.12
p.ygrid.grid_line_dash = [4, 4]

# Clean frame
p.outline_line_color = None
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#cccccc"
p.yaxis.axis_line_color = "#cccccc"
p.xaxis.major_tick_line_width = 0
p.yaxis.major_tick_line_width = 0
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.toolbar_location = None

# Background styling
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Margins
p.min_border_left = 140
p.min_border_bottom = 120
p.min_border_right = 80
p.min_border_top = 60

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
