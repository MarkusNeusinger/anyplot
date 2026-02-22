""" pyplots.ai
bump-basic: Basic Bump Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 76/100 | Updated: 2026-02-22
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure


# Data - Sports league standings over a season
entities = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta", "Team Epsilon"]
periods = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]

# Rankings for each team across weeks (1 = best)
rankings = {
    "Team Alpha": [3, 2, 1, 1, 2, 1],
    "Team Beta": [1, 1, 2, 3, 3, 4],
    "Team Gamma": [5, 4, 4, 2, 1, 2],
    "Team Delta": [2, 3, 3, 4, 4, 3],
    "Team Epsilon": [4, 5, 5, 5, 5, 5],
}

# Cohesive palette starting with Python Blue
colors = ["#306998", "#E6894A", "#5BA67D", "#C75A5A", "#8B6DB0"]

# Create figure with inverted y-axis (rank 1 at top)
p = figure(
    width=4800,
    height=2700,
    title="bump-basic · bokeh · pyplots.ai",
    x_range=periods,
    y_range=(5.5, 0.5),
    x_axis_label="Week",
    y_axis_label="Rank",
    toolbar_location=None,
)

# Plot lines and markers for each entity
legend_items = []
for i, (entity, ranks) in enumerate(rankings.items()):
    source = ColumnDataSource(data={"x": periods, "y": ranks, "team": [entity] * len(periods)})

    line = p.line(x="x", y="y", source=source, line_width=6, line_color=colors[i], line_alpha=0.8)
    scatter = p.scatter(x="x", y="y", source=source, size=28, color=colors[i], alpha=0.9)

    legend_items.append((entity, [line, scatter]))

# HoverTool for interactivity
hover = HoverTool(tooltips=[("Team", "@team"), ("Rank", "@y")])
p.add_tools(hover)

# Legend outside the plot
legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "24pt"
legend.glyph_width = 40
legend.glyph_height = 30
legend.spacing = 16
legend.border_line_color = None
p.add_layout(legend, "right")

# Title styling
p.title.text_font_size = "28pt"

# Axis styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle solid lines
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Save as PNG
export_png(p, filename="plot.png")
