""" pyplots.ai
bump-basic: Basic Bump Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-22
"""

import pygal
from pygal.style import Style


# Data - Formula 1 constructor standings across a 6-race season
entities = ["Red Bull Racing", "McLaren", "Ferrari", "Mercedes", "Aston Martin"]
periods = ["Bahrain", "Jeddah", "Melbourne", "Imola", "Monaco", "Barcelona"]

# Rankings for each constructor across race weekends (1 = best)
# Red Bull dominates early then McLaren surges to take the lead
rankings = {
    "Red Bull Racing": [1, 1, 2, 2, 3, 3],
    "McLaren": [4, 3, 1, 1, 1, 1],
    "Ferrari": [2, 2, 3, 3, 2, 2],
    "Mercedes": [3, 4, 4, 4, 4, 4],
    "Aston Martin": [5, 5, 5, 5, 5, 5],
}

max_rank = len(entities)

# Refined palette: warm tones for falling teams, cool tones for rising teams
# McLaren (rising protagonist) = bold orange, Red Bull (falling) = deep navy
# Intentional warm/cool contrast reinforces the narrative
custom_style = Style(
    background="white",
    plot_background="#FAFAFA",
    foreground="#2D2D2D",
    foreground_strong="#1A1A1A",
    foreground_subtle="#E8E8E8",
    colors=(
        "#1E3A5F",  # Red Bull - deep navy (falling from lead)
        "#FF8C00",  # McLaren - bold orange (rising protagonist)
        "#C0392B",  # Ferrari - classic red (steady runner-up)
        "#00A38D",  # Mercedes - teal (stable midfield)
        "#9B9B9B",  # Aston Martin - muted gray (distant 5th)
    ),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=40,
    value_font_size=36,
    opacity=0.90,
    opacity_hover=1.0,
    transition="200ms ease-in",
)

# Invert rankings so rank 1 appears at top of chart
inverted_rankings = {e: [max_rank + 1 - r for r in ranks] for e, ranks in rankings.items()}

# Visual hierarchy: protagonist lines (McLaren rising, Red Bull falling) are bolder
stroke_widths = {"Red Bull Racing": 10, "McLaren": 12, "Ferrari": 6, "Mercedes": 5, "Aston Martin": 4}
dot_sizes = {"Red Bull Racing": 16, "McLaren": 18, "Ferrari": 12, "Mercedes": 10, "Aston Martin": 8}

chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="bump-basic · pygal · pyplots.ai",
    x_title="Grand Prix",
    y_title="Constructor Standing",
    show_dots=True,
    dots_size=14,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    truncate_legend=-1,
    show_legend=True,
    interpolate=None,
    min_scale=1,
    max_scale=max_rank,
    margin=60,
    value_formatter=lambda v: f"P{max_rank + 1 - int(v)}" if v == int(v) else "",
    tooltip_border_radius=10,
    tooltip_fancy_mode=True,
    human_readable=True,
    pretty_print=True,
)

chart.x_labels = periods

# Custom y-axis labels showing actual rank positions
chart.y_labels = [{"value": max_rank + 1 - i, "label": f"P{i}"} for i in range(1, max_rank + 1)]

# Add each constructor with differentiated stroke width for visual hierarchy
for entity in entities:
    chart.add(
        entity, inverted_rankings[entity], stroke_style={"width": stroke_widths[entity]}, dots_size=dot_sizes[entity]
    )

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
