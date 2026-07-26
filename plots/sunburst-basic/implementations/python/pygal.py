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

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233")

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_label_font_size=38,
    stroke_width=3,
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
    (
        "Business",
        "#C475FD",
        [("Sales", "#C475FD", 150), ("Finance", "#D195FE", 100), ("Legal", "#DEB5FE", 60)],
    ),  # imprint lavender family
    (
        "Operations",
        "#4467A3",
        [("IT Support", "#4467A3", 90), ("Human Resources", "#7A93BD", 80)],
    ),  # imprint blue family
    (
        "Marketing",
        "#BD8233",
        [("Brand Design", "#BD8233", 60), ("Digital Marketing", "#D1A668", 40)],
    ),  # imprint ochre family
]

# pygal.Pie with multiple series simulates a sunburst: pygal always draws a
# multi-series pie in "dual" mode, so each series gets a full-radius solid
# aggregate wedge (the coarse hierarchy) plus a thin outer ring slice per
# datum (the fine-grained detail) — inner_radius has no effect here, so it's
# omitted rather than left as a misleading dead parameter.
chart = pygal.Pie(
    style=custom_style,
    width=2400,
    height=2400,
    title="sunburst-basic · python · pygal · anyplot.ai",
    show_legend=False,
    print_labels=True,
    print_values=False,
    margin=40,
    margin_right=320,
)

# Departments: coarse aggregate wedges, one per department — all 4 are major,
# so all get a printed label
chart.add(
    "Departments",
    [{"value": sum(v for _, _, v in teams), "label": name, "color": color} for name, color, teams in departments],
)

# Teams: fine-grained detail ring, shades of their parent department color.
# Only the largest team per department (teams are listed largest-first) is
# a printed label — the rest stay legible via HTML hover only (`tooltip`),
# avoiding a cluttered ring of ten overlapping labels. Technology is the
# exception: its largest team starts exactly where the Departments ring's
# "Marketing" label ends, so its 2nd-largest team is printed instead to
# keep the two labels from colliding at that ring seam.
chart.add(
    "Teams",
    [
        {
            "value": value,
            "color": color,
            **({"label": name} if rank == (1 if dept_index == 0 else 0) else {"tooltip": name}),
        }
        for dept_index, (_, _, teams) in enumerate(departments)
        for rank, (name, color, value) in enumerate(teams)
    ],
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
