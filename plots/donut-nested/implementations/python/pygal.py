""" anyplot.ai
donut-nested: Nested Donut Chart
Library: pygal 3.1.3 | Python 3.13.15
Quality: 69/100 | Updated: 2026-08-18
"""

import os
import re

import cairosvg
import pygal
from pygal.style import Style


def lerp_hex(c0, c1, t):
    """Interpolate between two hex colors (see default-style-guide.md continuous-data lerp)."""
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(round(a + (b - a) * t)) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — one hue family per department, canonical order
# since departments are abstract organizational units (no semantic color cue).
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233")

# Data: annual budget allocation by department (inner ring) and expense
# category within each department (outer ring), in $K. Every department has
# the same number of categories so pygal's dual-series pie doesn't need to
# zero-pad shorter series.
budget = {
    "Engineering": {"Salaries": 850, "Cloud Infrastructure": 220, "Software Licenses": 90, "R&D Equipment": 140},
    "Marketing": {
        "Digital Advertising": 280,
        "Events & Trade Shows": 150,
        "Content Production": 90,
        "Marketing Analytics": 60,
    },
    "Operations": {"Facilities": 260, "Logistics": 150, "Equipment Maintenance": 80, "Safety & Compliance": 50},
    "Sales": {"Commissions": 380, "Travel": 120, "CRM Tools": 60, "Sales Training": 40},
}

# Each department's categories get a shared hue tinted toward the elevated
# surface color, lightest-first by descending value — consistent color
# families per parent, varying lightness for children (spec requirement).
TINT_STEPS = (0.30, 0.48, 0.62, 0.75)

# Plot — pygal's Pie renders a native two-level "dual" donut when a series
# carries multiple values: each department becomes a full inner wedge, and
# its categories become a thin outer ring aligned to the same angular span.
title = "donut-nested · python · pygal · anyplot.ai"
title_font_size = round(66 * min(1.0, 67 / len(title)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    opacity=1,
    opacity_hover=1,
)

chart = pygal.Pie(
    width=2400,
    height=2400,
    style=custom_style,
    title=title,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    print_labels=True,
    value_formatter=lambda v: f"${v}K",
    margin=90,
)

for i, (department, categories) in enumerate(budget.items()):
    base = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    ordered = sorted(categories.items(), key=lambda kv: kv[1], reverse=True)
    values = [
        {
            "value": amount,
            # pygal's dual pie leaks the last category's metadata onto the
            # department's own aggregate wedge; leaving the smallest
            # category unlabeled avoids that mislabel while its value still
            # prints (angle permitting).
            "label": category if rank < len(ordered) - 1 else "",
            "color": lerp_hex(base, ELEVATED_BG, TINT_STEPS[rank % len(TINT_STEPS)]),
        }
        for rank, (category, amount) in enumerate(ordered)
    ]
    chart.add(department, values)

# Save — pygal has no native donut hole for the inner ring of a dual pie, so
# punch one by overlaying a page-background circle at the shared wedge
# center (read back from the rendered geometry, never guessed) onto the
# already-rendered SVG. Both plot-{THEME}.png and plot-{THEME}.html are
# rasterized/written from this same markup for perfect visual parity.
svg_markup = chart.render().decode("utf-8")
center_match = re.search(
    r'class="big_slice"><path d="M[\d.]+ [\d.]+ A([\d.]+) [\d.]+ 0 \d \d '
    r"[\d.]+ [\d.]+ L([\d.]+) ([\d.]+)",
    svg_markup,
)
outer_radius, center_x, center_y = (float(g) for g in center_match.groups())
hole_radius = outer_radius * 0.55
hole = f'<circle cx="{center_x}" cy="{center_y}" r="{hole_radius}" fill="{PAGE_BG}" stroke="none"/>'
svg_markup = svg_markup.replace("</svg>", f"{hole}</svg>")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_markup)

cairosvg.svg2png(bytestring=svg_markup.encode("utf-8"), write_to=f"plot-{THEME}.png")
