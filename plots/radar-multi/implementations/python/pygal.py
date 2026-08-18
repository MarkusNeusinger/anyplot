""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: pygal 3.1.3 | Python 3.13.15
Quality: 90/100 | Updated: 2026-08-17
"""

import os

import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — position 1 is always the brand green
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data - Team performance comparison across skill dimensions
categories = ["Communication", "Technical", "Leadership", "Creativity", "Teamwork", "Problem Solving"]
teams = [
    ("Alpha Team", [85, 90, 75, 80, 88, 82]),
    ("Beta Team", [78, 72, 85, 90, 70, 88]),
    ("Gamma Team", [65, 88, 70, 75, 92, 78]),
]

# Highest overall average becomes the visual "hero" series — a bolder, solid
# stroke and larger dots build a focal point so the viewer immediately spots
# the top all-round team, while the other two recede behind a thinner dashed
# outline.
hero_name, _ = max(teams, key=lambda t: sum(t[1]) / len(t[1]))

# Style — theme-adaptive chrome, Imprint palette, sizing tuned for the 2400x2400 canvas
custom_style = Style(
    font_family='"Liberation Sans", "DejaVu Sans", Arial, sans-serif',
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.25,
    opacity_hover=0.5,
)

# Plot — square canvas for the symmetric radar layout. Legend moved to the
# bottom (rather than the default left column) so the polar plot area is no
# longer squeezed toward the top-right of the canvas, balancing whitespace.
chart = pygal.Radar(
    width=2400,
    height=2400,
    style=custom_style,
    title="radar-multi · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_dots=True,
    fill=True,
    inner_radius=0.1,
    range=(0, 100),
    margin=30,
    spacing=16,
)
chart.x_labels = categories

# Add data series — hero team gets a bold solid stroke + larger dots, the
# other two recede behind a thinner dashed outline.
for team_name, values in teams:
    is_hero = team_name == hero_name
    chart.add(
        team_name,
        values,
        dots_size=12 if is_hero else 7,
        stroke_style={"width": 6, "linecap": "round", "linejoin": "round"}
        if is_hero
        else {"width": 2.5, "linecap": "round", "linejoin": "round", "dasharray": "12,6"},
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
