""" pyplots.ai
bump-basic: Basic Bump Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-22
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Legend
from bokeh.plotting import figure


# Data - Formula 1 constructor standings over a 6-race stretch
entities = ["Red Bull Racing", "McLaren", "Ferrari", "Mercedes", "Aston Martin"]
periods = ["Race 1", "Race 2", "Race 3", "Race 4", "Race 5", "Race 6"]

# Rankings for each team across races (1 = best)
rankings = {
    "Red Bull Racing": [3, 2, 1, 1, 2, 1],
    "McLaren": [1, 1, 2, 3, 3, 4],
    "Ferrari": [5, 4, 4, 2, 1, 2],
    "Mercedes": [2, 3, 3, 4, 4, 3],
    "Aston Martin": [4, 5, 5, 5, 5, 5],
}

# Cohesive palette starting with Python Blue — colorblind-safe
colors = ["#306998", "#E6894A", "#D44D5C", "#5BA67D", "#8B6DB0"]

# Emphasis: highlight the two teams with dramatic rank changes
# Ferrari rises from 5th to 1st; McLaren falls from 1st to 4th
highlight = {"Ferrari", "Red Bull Racing", "McLaren"}

# Create figure with inverted y-axis (rank 1 at top)
p = figure(
    width=4800,
    height=2700,
    title="bump-basic · bokeh · pyplots.ai",
    x_range=periods,
    y_range=(5.8, 0.4),
    x_axis_label="Constructor Standings by Race",
    y_axis_label="Championship Position",
    toolbar_location=None,
)

# Plot lines and markers for each entity with visual hierarchy
legend_items = []
for i, (entity, ranks) in enumerate(rankings.items()):
    source = ColumnDataSource(data={"x": periods, "y": ranks, "team": [entity] * len(periods)})

    is_highlight = entity in highlight
    lw = 10 if is_highlight else 5
    alpha_line = 0.95 if is_highlight else 0.35
    alpha_marker = 1.0 if is_highlight else 0.4
    marker_size = 38 if is_highlight else 22

    line = p.line(x="x", y="y", source=source, line_width=lw, line_color=colors[i], line_alpha=alpha_line)
    scatter = p.scatter(x="x", y="y", source=source, size=marker_size, color=colors[i], alpha=alpha_marker)

    legend_items.append((entity, [line, scatter]))

    # End-of-line labels using Bokeh's Label annotation
    label = Label(
        x=5,
        y=ranks[-1],
        text=entity,
        text_font_size="20pt",
        text_color=colors[i],
        text_alpha=alpha_line,
        text_font_style="bold" if is_highlight else "normal",
        x_offset=18,
        y_offset=-8,
    )
    p.add_layout(label)

# Legend outside the plot
legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "22pt"
legend.glyph_width = 50
legend.glyph_height = 35
legend.spacing = 18
legend.border_line_color = None
legend.background_fill_alpha = 0
legend.padding = 20
p.add_layout(legend, "right")

# Title styling
p.title.text_font_size = "32pt"
p.title.text_font_style = "bold"
p.title.text_color = "#2c3e50"

# Axis styling
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.axis_label_text_color = "#555555"
p.yaxis.axis_label_text_color = "#555555"
p.xaxis.major_label_text_color = "#444444"
p.yaxis.major_label_text_color = "#444444"

# Remove spines for clean look
p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid styling - subtle dashed lines
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.25
p.ygrid.grid_line_dash = [4, 4]

# Y-axis ticks at integer rank positions only
p.yaxis.ticker = [1, 2, 3, 4, 5]

# Background
p.background_fill_color = "#f8f9fa"
p.border_fill_color = "white"
p.outline_line_color = None

# Generous padding for balanced layout
p.min_border_left = 100
p.min_border_right = 60
p.min_border_top = 80
p.min_border_bottom = 80

# Save as PNG
export_png(p, filename="plot.png")
