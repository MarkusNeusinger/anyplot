""" pyplots.ai
bump-basic: Basic Bump Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Updated: 2026-02-22
"""

import pygal
from pygal.style import Style


# Data - Sports league standings over a season
entities = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta", "Team Epsilon"]
periods = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]

# Rankings for each team across periods (1 = best)
# Dramatic position swaps: Alpha rises from 4th to 1st, Beta collapses, Gamma surges late
rankings = {
    "Team Alpha": [4, 3, 2, 1, 1, 1],
    "Team Beta": [1, 1, 3, 4, 5, 4],
    "Team Gamma": [2, 4, 4, 3, 2, 2],
    "Team Delta": [3, 2, 1, 2, 3, 3],
    "Team Epsilon": [5, 5, 5, 5, 4, 5],
}

# Custom style for pyplots (4800 x 2700 px target)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#D4A017", "#2ecc71", "#E8875B", "#8B6FBF"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=8,
    opacity=0.85,
    opacity_hover=1.0,
    transition="200ms ease-in",
)

# Create bump chart - invert rankings to show rank 1 at top
# Transform: rank -> (max_rank + 1 - rank) so rank 1 becomes 5, rank 5 becomes 1
max_rank = len(entities)
inverted_rankings = {entity: [max_rank + 1 - r for r in ranks] for entity, ranks in rankings.items()}

# Create chart using Line with pygal interactive features
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="bump-basic · pygal · pyplots.ai",
    x_title="Period",
    y_title="Rank",
    show_dots=True,
    dots_size=14,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    truncate_legend=-1,
    show_legend=True,
    interpolate=None,
    min_scale=1,
    max_scale=max_rank,
    margin=50,
    value_formatter=lambda v: f"Rank {max_rank + 1 - int(v)}" if v == int(v) else "",
    tooltip_border_radius=10,
    tooltip_fancy_mode=True,
    human_readable=True,
    pretty_print=True,
)

# Set x-axis labels
chart.x_labels = periods

# Custom y-axis labels (inverted: 5 displays as 1, 1 displays as 5)
chart.y_labels = [{"value": max_rank + 1 - i, "label": str(i)} for i in range(1, max_rank + 1)]

# Add each team's inverted ranking as a series
for entity in entities:
    chart.add(entity, inverted_rankings[entity])

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
