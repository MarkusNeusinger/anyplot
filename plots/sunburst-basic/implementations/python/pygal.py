""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 73/100 | Created: 2026-05-04
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=40,
    value_font_size=32,
    stroke_width=2,
)

# Organizational budget breakdown (in $K)
# Each department: (name, primary_color, [(team, team_color, value), ...])
# Team colors are shades of their parent department color
departments = [
    (
        "Technology",
        "#009E73",
        [
            ("Backend Engineering", "#009E73", 180),
            ("Frontend Engineering", "#40B88E", 140),
            ("Data Science", "#7DD3AB", 100),
        ],
    ),
    ("Business", "#D55E00", [("Sales", "#D55E00", 150), ("Finance", "#E07D33", 100), ("Legal", "#EB9C66", 60)]),
    ("Operations", "#0072B2", [("IT Support", "#0072B2", 90), ("Human Resources", "#3396C8", 80)]),
    ("Marketing", "#CC79A7", [("Brand Design", "#CC79A7", 60), ("Digital Marketing", "#D99ABD", 40)]),
]

# pygal.Pie with multiple series creates concentric rings — a sunburst chart
# inner_radius=0.4 creates a donut; first series = inner ring (departments)
chart = pygal.Pie(
    style=custom_style,
    width=3600,
    height=3600,
    title="sunburst-basic · pygal · anyplot.ai",
    inner_radius=0.4,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=False,
)

# Inner ring: department totals — each slice color matches the department
chart.add(
    "Departments",
    [{"value": sum(v for _, _, v in teams), "label": name, "color": color} for name, color, teams in departments],
)

# Outer ring: individual teams — shades of their parent department color
chart.add(
    "Teams",
    [{"value": value, "label": name, "color": color} for _, _, teams in departments for name, color, value in teams],
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
