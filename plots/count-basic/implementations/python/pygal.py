"""anyplot.ai
count-basic: Basic Count Plot
Library: pygal 3.1.3 | Python 3.13.14
Quality: 90/100 | Updated: 2026-08-11
"""

import os
import sys
from collections import Counter


# Work around naming conflict: pygal.py filename shadows pygal package
sys.path.pop(0)

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")


# Semantic anchors reused for the sentiment scale below (Imprint palette
# "Semantic exception": positive -> green, negative -> red, neutral -> muted).
# Each polarity gets two shades so the two intensity levels ("Dissatisfied"
# vs "Very Dissatisfied", "Satisfied" vs "Very Satisfied") stay visually
# distinguishable while keeping the hue. The style guide forbids inventing
# custom hex literals for this, so the lighter shade is an alpha-tinted rgba()
# of the same Imprint hex rather than a new hex value -- the full-strength
# hex is reserved for the "Very" (most intense) category.
def _rgba(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


POSITIVE = _rgba(IMPRINT[0], 0.6)  # tinted brand green, "Satisfied"
POSITIVE_STRONG = IMPRINT[0]  # full-strength brand green, "Very Satisfied"
NEGATIVE = _rgba(IMPRINT[4], 0.6)  # tinted matte red, "Dissatisfied"
NEGATIVE_STRONG = IMPRINT[4]  # full-strength matte red, "Very Dissatisfied"
NEUTRAL = INK_MUTED  # theme-adaptive muted anchor

# Data - Survey responses from customer feedback
responses = [
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Dissatisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Dissatisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
]

# Count occurrences
counts = Counter(responses)
total = len(responses)

# Define category order (logical satisfaction order) and its sentiment color
category_order = ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"]
category_sentiment = {
    "Very Dissatisfied": NEGATIVE_STRONG,
    "Dissatisfied": NEGATIVE,
    "Neutral": NEUTRAL,
    "Satisfied": POSITIVE,
    "Very Satisfied": POSITIVE_STRONG,
}

# Custom style, sized for the 3200x1800 canvas (see prompts/library/pygal.md
# "Sizing + Theme" - unitless pygal sizes map ~1:1 onto source pixels)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    # Print-value text otherwise defaults to black/white per bar-fill
    # luminance (pygal's Style.value_colors heuristic) rather than the
    # theme-adaptive ink used everywhere else -- pin it to INK so the counts
    # stay legible against the plot background in both themes.
    value_colors=(INK,),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=32,
    stroke_width=2.5,
    # Style guide requires solid (not dashed) y-guides at low opacity;
    # pygal defaults to a dashed stroke, so force it off here.
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
)

# Create chart
chart = pygal.Bar(
    width=3200,
    height=1800,
    style=custom_style,
    title="count-basic · python · pygal · anyplot.ai",
    x_title="Satisfaction Level",
    y_title="Number of Responses",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: str(int(x)),
    rounded_bars=8,
    margin=50,
    spacing=60,
    x_label_rotation=30,
)

# Set x-axis labels
chart.x_labels = category_order

# Advanced pygal technique: per-bar metadata gives each category a sentiment
# color (Imprint semantic exception: positive->green, negative->red,
# neutral->muted) and a hover tooltip with the response share, instead of a
# single flat series color.
chart.add(
    "Responses",
    [
        {
            "value": counts.get(cat, 0),
            "color": category_sentiment[cat],
            "tooltip": f"{cat}: {counts.get(cat, 0)} responses ({counts.get(cat, 0) / total:.0%})",
        }
        for cat in category_order
    ],
)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
