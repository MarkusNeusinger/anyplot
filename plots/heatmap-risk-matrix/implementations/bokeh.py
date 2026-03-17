"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, LabelSet, LinearColorMapper, Range1d
from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.transform import transform


# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Build background grid with risk scores (using numeric coords)
grid_x = []
grid_y = []
risk_scores = []
score_text = []

for i in range(5):
    for j in range(5):
        grid_x.append(j + 0.5)
        grid_y.append(i + 0.5)
        score = (i + 1) * (j + 1)
        risk_scores.append(score)
        score_text.append(str(score))

grid_source = ColumnDataSource(data={"x": grid_x, "y": grid_y, "score": risk_scores, "text": score_text})

# Color mapper: green (low) -> yellow -> orange -> red (critical)
risk_palette = [
    "#2D8A4E",
    "#4CAF50",
    "#8BC34A",
    "#CDDC39",
    "#FFEB3B",
    "#FFC107",
    "#FF9800",
    "#FF5722",
    "#E53935",
    "#B71C1C",
]
mapper = LinearColorMapper(palette=risk_palette, low=1, high=25)

# Risk items
risks = [
    ("Server Outage", 3, 4, "Technical"),
    ("Data Breach", 2, 5, "Technical"),
    ("Budget Overrun", 4, 3, "Financial"),
    ("Key Staff Loss", 3, 3, "Operational"),
    ("Vendor Failure", 2, 4, "Operational"),
    ("Scope Creep", 4, 2, "Financial"),
    ("Regulatory Change", 2, 3, "Legal"),
    ("Market Shift", 3, 5, "Financial"),
    ("Power Failure", 1, 4, "Technical"),
    ("Supply Delay", 3, 2, "Operational"),
    ("Cyber Attack", 2, 5, "Technical"),
    ("Contract Dispute", 1, 3, "Legal"),
    ("Skill Gap", 4, 2, "Operational"),
    ("Currency Risk", 3, 3, "Financial"),
    ("System Migration", 2, 4, "Technical"),
]

cat_colors = {"Technical": "#1A237E", "Financial": "#4A148C", "Operational": "#004D40", "Legal": "#BF360C"}

# Apply jitter to numeric coordinates
jitter_vals = np.random.uniform(-0.28, 0.28, size=(len(risks), 2))
risk_x = []
risk_y = []
risk_names = []
risk_marker_colors = []

for idx, (name, likelihood, impact, category) in enumerate(risks):
    risk_x.append(impact - 1 + 0.5 + jitter_vals[idx, 0])
    risk_y.append(likelihood - 1 + 0.5 + jitter_vals[idx, 1])
    risk_names.append(name)
    risk_marker_colors.append(cat_colors[category])

risk_source = ColumnDataSource(data={"x": risk_x, "y": risk_y, "label": risk_names, "color": risk_marker_colors})

# Plot — extend x_range to make room for legend on the right
p = figure(
    width=4800,
    height=2700,
    x_range=Range1d(0, 7.2),
    y_range=Range1d(0, 5),
    title="heatmap-risk-matrix · bokeh · pyplots.ai",
    toolbar_location=None,
)

# Background heatmap cells
p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=grid_source,
    fill_color=transform("score", mapper),
    line_color="white",
    line_width=4,
)

# Risk score watermark in each cell
p.text(
    x="x",
    y="y",
    text="text",
    source=grid_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="28pt",
    text_color="#00000020",
    text_font_style="bold",
)

# Risk markers
p.scatter(x="x", y="y", source=risk_source, size=30, color="color", line_color="white", line_width=2.5, alpha=0.9)

# Risk name labels
labels = LabelSet(
    x="x",
    y="y",
    text="label",
    source=risk_source,
    x_offset=0,
    y_offset=-24,
    text_align="center",
    text_baseline="top",
    text_font_size="14pt",
    text_color="#222222",
    text_font_style="bold",
    background_fill_color="white",
    background_fill_alpha=0.7,
)
p.add_layout(labels)

# Custom tick labels for categorical axes
p.xaxis.ticker = [0.5, 1.5, 2.5, 3.5, 4.5]
p.yaxis.ticker = [0.5, 1.5, 2.5, 3.5, 4.5]
p.xaxis.major_label_overrides = {0.5: "Negligible", 1.5: "Minor", 2.5: "Moderate", 3.5: "Major", 4.5: "Catastrophic"}
p.yaxis.major_label_overrides = {0.5: "Rare", 1.5: "Unlikely", 2.5: "Possible", 3.5: "Likely", 4.5: "Almost Certain"}

# Zone legend (using data coordinates in the extended right area)
zone_data = [
    ("Low (1-4)", "#2D8A4E"),
    ("Medium (5-9)", "#9E9D24"),
    ("High (10-16)", "#FF9800"),
    ("Critical (20-25)", "#B71C1C"),
]
p.add_layout(
    Label(x=5.3, y=4.8, text="Risk Zones", text_font_size="18pt", text_font_style="bold", text_color="#333333")
)
for idx, (zone_label, zone_color) in enumerate(zone_data):
    p.add_layout(
        Label(
            x=5.3,
            y=4.4 - idx * 0.35,
            text=zone_label,
            text_font_size="16pt",
            text_color=zone_color,
            text_font_style="bold",
        )
    )

# Category legend
p.add_layout(
    Label(x=5.3, y=2.8, text="Categories", text_font_size="18pt", text_font_style="bold", text_color="#333333")
)
for idx, (cat_name, cat_color) in enumerate(cat_colors.items()):
    p.scatter(x=[5.45], y=[2.4 - idx * 0.35], size=18, color=cat_color, line_color="white", line_width=1.5, alpha=0.9)
    p.add_layout(
        Label(
            x=5.6,
            y=2.4 - idx * 0.35,
            text=cat_name,
            text_font_size="15pt",
            text_color=cat_color,
            text_font_style="bold",
            y_offset=-10,
        )
    )

# Style
p.title.text_font_size = "28pt"
p.title.align = "center"
p.xaxis.axis_label = "Impact"
p.yaxis.axis_label = "Likelihood"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.grid.grid_line_color = None
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Risk Assessment Matrix")
