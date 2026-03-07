""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-04
"""

import re
from xml.etree import ElementTree as ET

import cairosvg
import pygal
from pygal.style import Style


# Data - Employee engagement survey (8 questions, 5-point Likert scale)
questions = [
    "I feel valued at work",
    "My manager provides clear direction",
    "I have opportunities for growth",
    "Work-life balance is supported",
    "I receive fair compensation",
    "Team collaboration is effective",
    "Company vision is inspiring",
    "My contributions are recognized",
]

# Response percentages: (Strongly Disagree, Disagree, Neutral, Agree, Strongly Agree)
# Includes strongly negative (compensation, vision) and strongly positive (collaboration)
responses = [
    (5, 10, 15, 40, 30),
    (8, 15, 20, 35, 22),
    (12, 22, 18, 30, 18),
    (6, 12, 22, 38, 22),
    (22, 30, 18, 20, 10),
    (3, 7, 10, 42, 38),
    (18, 28, 22, 22, 10),
    (7, 14, 16, 38, 25),
]

# Sort by net agreement for easy comparison
net_scores = [(r[3] + r[4]) - (r[0] + r[1]) for r in responses]
order = sorted(range(len(questions)), key=lambda i: net_scores[i])
questions = [questions[i] for i in order]
responses = [responses[i] for i in order]

# Diverging color palette: ColorBrewer RdBu 5-class (colorblind-safe)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="white",
    colors=("#D9D9D9", "#EF8A62", "#B2182B", "#D9D9D9", "#67A9CF", "#2166AC"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=30,
    value_label_font_size=30,
    tooltip_font_size=30,
)

# Build diverging series (neutral split evenly at center)
neutral_left = [-r[2] / 2 for r in responses]
disagree_vals = [-r[1] for r in responses]
strongly_disagree_vals = [-r[0] for r in responses]
neutral_right = [r[2] / 2 for r in responses]
agree_vals = [r[3] for r in responses]
strongly_agree_vals = [r[4] for r in responses]

# Chart
chart = pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Employee Engagement Survey · bar-diverging-likert · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_x_guides=False,
    show_y_guides=False,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{abs(x):.0f}%" if abs(x) >= 8 else "",
    x_title="Response Percentage (%)",
    margin=50,
    spacing=15,
    truncate_label=-1,
    truncate_legend=-1,
)

# Add series from center outward
# Negative side: neutral half → disagree → strongly disagree
chart.add("Neutral", neutral_left)
chart.add("Disagree", disagree_vals)
chart.add("Strongly Disagree", strongly_disagree_vals)
# Positive side: neutral half → agree → strongly agree
chart.add(None, neutral_right)
chart.add("Agree", agree_vals)
chart.add("Strongly Agree", strongly_agree_vals)

chart.x_labels = questions

# Render SVG and strip guide lines (pygal renders them despite show_x_guides=False)
svg_content = chart.render().decode("utf-8")

# Remove guide line paths but keep axis text labels
svg_content = re.sub(r'<path [^>]*class="(?:major )?(?:axis major )?guide line"[^/]*/>', "", svg_content)

# Reorder legend from stacking order (N, D, SD, A, SA) to Likert scale order (SD, D, N, A, SA)
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_content)

serie_0 = root.find(f'.//{{{SVG_NS}}}g[@id="activate-serie-0"]')
serie_2 = root.find(f'.//{{{SVG_NS}}}g[@id="activate-serie-2"]')
if serie_0 is not None and serie_2 is not None:
    for child_0, child_2 in zip(serie_0, serie_2, strict=False):
        x0, x2 = child_0.get("x"), child_2.get("x")
        if x0 is not None and x2 is not None:
            child_0.set("x", x2)
            child_2.set("x", x0)

svg_content = ET.tostring(root, encoding="unicode")

# Save as PNG and HTML
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")

with open("plot.html", "w") as f:
    f.write(svg_content)
