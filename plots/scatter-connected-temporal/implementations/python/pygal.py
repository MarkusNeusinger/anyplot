"""anyplot.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-06-09
"""

import os
import re
import sys


# Remove script's own directory from sys.path so the real pygal package is found first
_here = os.path.dirname(os.path.abspath(__file__))
if _here in sys.path:
    sys.path.remove(_here)

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — amber semantic anchor for key events
ANYPLOT_AMBER = "#DDCC77"

# Data — fertility rate vs urbanization for an emerging economy (1980–2023)
np.random.seed(42)
years = list(range(1980, 2024))
n_years = len(years)

urban_step = np.random.normal(0.95, 0.3, n_years)
urban_step[20:24] = np.random.normal(-0.1, 0.2, 4)  # 2000–2003 stalled migration
urbanization = 28 + np.cumsum(urban_step)

fert_step = np.random.normal(-0.075, 0.03, n_years)
fert_step[35:38] += 0.17  # 2015–2017 pronatalist rebound
fertility = np.clip(5.6 + np.cumsum(fert_step), 1.2, 7.0)


def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    return "#{:02X}{:02X}{:02X}".format(*(round(a + (b - a) * t) for a, b in ((r0, r1), (g0, g1), (b0, b1))))


# Imprint imprint_seq gradient (#009E73 -> #4467A3) for temporal progression
era_bounds = [(0, 10), (10, 20), (20, 30), (30, 37), (37, 43)]
era_colors = [_lerp_hex("#009E73", "#4467A3", i / (len(era_bounds) - 1)) for i in range(len(era_bounds))]
eras = [(f"{years[s]}–{years[e]}", s, e, c) for (s, e), c in zip(era_bounds, era_colors, strict=True)]

annotate_years = {1990, 2000, 2010, 2020}

# Title scaled for 81-char length: round(66 × 67/81) = 55
title = "Fertility vs Urbanization · scatter-connected-temporal · python · pygal · anyplot.ai"
title_font_size = max(44, round(66 * 67 / len(title)))

font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="3,5",
    colors=(*era_colors, ANYPLOT_AMBER, "#AE3030", "#4467A3"),
    font_family=font,
    title_font_family=font,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_label_font_size=44,
    tooltip_font_size=36,
    tooltip_font_family=font,
    opacity=0.92,
    opacity_hover=1.0,
    stroke_width=5,
    stroke_opacity=0.9,
    stroke_opacity_hover=1.0,
)

x_min = float(np.floor(urbanization.min() / 5) * 5)
x_max = float(np.ceil(urbanization.max() / 5) * 5)
y_min = float(np.floor(fertility.min() * 2) / 2)
y_max = float(np.ceil(fertility.max() * 2) / 2)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Urban Population (% of total)",
    y_title="Fertility Rate (births per woman)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=28,
    stroke=True,
    dots_size=12,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.0f}%",
    value_formatter=lambda y: f"{y:.1f}",
    print_labels=True,
    print_values=False,
    margin_bottom=130,
    margin_left=80,
    margin_right=140,
    margin_top=90,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
    x_labels_major_count=8,
    y_labels_major_count=8,
    js=[],
    show_x_labels=True,
    show_y_labels=True,
)

# Temporal path as Imprint imprint_seq gradient era segments
for era_name, start, end, color in eras:
    end_idx = min(end + 1, n_years)
    segment_points = [
        {"value": (float(urbanization[i]), float(fertility[i])), "color": color} for i in range(start, end_idx)
    ]
    chart.add(
        era_name,
        segment_points,
        stroke=True,
        show_dots=True,
        dots_size=12,
        stroke_style={"width": 5, "linecap": "round", "linejoin": "round"},
    )

# Key years highlighted with amber dots and year labels
annotated_points = []
for yr in sorted(annotate_years):
    i = yr - years[0]
    annotated_points.append(
        {"value": (float(urbanization[i]), float(fertility[i])), "label": str(yr), "color": ANYPLOT_AMBER}
    )
chart.add("Key years", annotated_points, stroke=False, dots_size=20)

# Start and end markers
chart.add(
    f"Start ({years[0]})",
    [{"value": (float(urbanization[0]), float(fertility[0])), "label": "▶ 1980", "color": "#AE3030"}],
    stroke=False,
    dots_size=26,
)
chart.add(
    f"End ({years[-1]})",
    [{"value": (float(urbanization[-1]), float(fertility[-1])), "label": "● 2023", "color": "#4467A3"}],
    stroke=False,
    dots_size=26,
)

# Patch label text colors for dark-theme legibility before PNG conversion
# pygal's print_labels text color does not adapt to the dark background via the foreground Style token
_label_texts = {str(yr) for yr in sorted(annotate_years)} | {"▶ 1980", "● 2023"}


def _patch_label_colors(svg_str, labels, fill_color):
    def _fix(m):
        tag_attrs, content = m.group(1), m.group(2)
        if content.strip() not in labels:
            return m.group(0)
        # inline style outranks pygal's `.label` CSS class fill
        return f'<text{tag_attrs} style="fill:{fill_color}">{content}</text>'

    return re.sub(r"<text([^>]*)>(.*?)</text>", _fix, svg_str, flags=re.DOTALL)


svg_data = chart.render()
svg_str = _patch_label_colors(svg_data.decode("utf-8"), _label_texts, INK)
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
