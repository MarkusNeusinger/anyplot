""" pyplots.ai
timeline-basic: Event Timeline
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.palettes import Category10
from bokeh.plotting import figure


# Data - Software project milestones
events = [
    ("2024-01-15", "Project Kickoff", "Planning"),
    ("2024-02-01", "Requirements Complete", "Planning"),
    ("2024-03-10", "Design Review", "Design"),
    ("2024-04-20", "Prototype Ready", "Development"),
    ("2024-05-15", "Alpha Release", "Development"),
    ("2024-06-30", "Beta Testing", "Testing"),
    ("2024-07-25", "Bug Fix Sprint", "Testing"),
    ("2024-08-15", "Performance Audit", "Testing"),
    ("2024-09-10", "Security Review", "Release"),
    ("2024-10-01", "v1.0 Launch", "Release"),
]

df = pd.DataFrame(events, columns=["date", "event", "category"])
df["date"] = pd.to_datetime(df["date"])

# Assign alternating y positions for label readability (above/below axis)
df["y_pos"] = [0.6 if i % 2 == 0 else -0.6 for i in range(len(df))]

# Category colors
categories = df["category"].unique().tolist()
color_map = {cat: Category10[10][i] for i, cat in enumerate(categories)}
df["color"] = df["category"].map(color_map)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="timeline-basic · bokeh · pyplots.ai",
    x_axis_type="datetime",
    y_range=(-1.5, 1.5),
    tools="",
    toolbar_location=None,
)

# Draw the central timeline axis (horizontal line)
p.line(
    x=[df["date"].min() - pd.Timedelta(days=10), df["date"].max() + pd.Timedelta(days=10)],
    y=[0, 0],
    line_width=6,
    line_color="#306998",
    line_alpha=0.8,
)

# Draw vertical connector lines and markers for each event
for _, row in df.iterrows():
    # Vertical connector line from axis to marker
    p.line(x=[row["date"], row["date"]], y=[0, row["y_pos"]], line_width=3, line_color=row["color"], line_alpha=0.7)

# Plot event markers with category colors
for cat in categories:
    cat_df = df[df["category"] == cat]
    cat_source = ColumnDataSource(cat_df)
    p.scatter(
        x="date",
        y="y_pos",
        source=cat_source,
        size=35,
        color=color_map[cat],
        alpha=0.9,
        marker="circle",
        legend_label=cat,
        line_color="white",
        line_width=3,
    )

# Add event labels manually with proper positioning
for _, row in df.iterrows():
    y_offset = 80 if row["y_pos"] > 0 else -80
    baseline = "bottom" if row["y_pos"] > 0 else "top"
    label = Label(
        x=row["date"],
        y=row["y_pos"],
        text=row["event"],
        text_font_size="18pt",
        text_color="#333333",
        text_align="center",
        text_baseline=baseline,
        y_offset=y_offset,
    )
    p.add_layout(label)

# Style the plot
p.title.text_font_size = "32pt"
p.title.text_color = "#306998"
p.title.align = "center"

p.xaxis.axis_label = "Date"
p.xaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_orientation = 0.4
p.xaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.xaxis.minor_tick_line_width = 1

p.yaxis.visible = False
p.ygrid.visible = False
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.xgrid.grid_line_width = 2

p.outline_line_color = None
p.background_fill_color = "#fafafa"

# Configure legend
p.legend.location = "top_right"
p.legend.title = "Phase"
p.legend.title_text_font_size = "22pt"
p.legend.label_text_font_size = "20pt"
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.border_line_color = "#cccccc"
p.legend.background_fill_alpha = 0.9
p.legend.padding = 15
p.legend.spacing = 10

# Save outputs
export_png(p, filename="plot.png")

# Also save HTML for interactive version
output_file("plot.html", title="Event Timeline")
save(p)
