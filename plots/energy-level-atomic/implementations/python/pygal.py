""" anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-30
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Spectral regions in wavelength order, one Imprint hue each: blue on the short-wave side,
# green in the middle of the visible band, matte red on the long-wave side
REGIONS = {
    "Lyman series · ultraviolet": "#4467A3",
    "Balmer series · visible": "#009E73",
    "Paschen series · infrared": "#AE3030",
}

# Data — Hydrogen atom spectral series
# Evenly-spaced visual y positions (nonlinear scale for converging upper levels)
visual_y = {1: 1.0, 2: 2.5, 3: 4.0, 4: 5.5, 5: 7.0, 6: 8.5}
energy_ev = {1: -13.60, 2: -3.40, 3: -1.51, 4: -0.85, 5: -0.54, 6: -0.38}
ionization_y = 10.0

# (upper level, lower level, label, x position, region)
transitions = [
    (2, 1, "Ly-α 122 nm", 2.0, "Lyman series · ultraviolet"),
    (3, 1, "Ly-β 103 nm", 2.7, "Lyman series · ultraviolet"),
    (4, 1, "Ly-γ 97 nm", 3.4, "Lyman series · ultraviolet"),
    (3, 2, "Hα 656 nm", 4.5, "Balmer series · visible"),
    (4, 2, "Hβ 486 nm", 5.2, "Balmer series · visible"),
    (5, 2, "Hγ 434 nm", 5.9, "Balmer series · visible"),
    (6, 2, "Hδ 410 nm", 6.6, "Balmer series · visible"),
    (4, 3, "Pa-α 1875 nm", 7.6, "Paschen series · infrared"),
    (5, 3, "Pa-β 1282 nm", 8.35, "Paschen series · infrared"),
    (6, 3, "Pa-γ 1094 nm", 9.1, "Paschen series · infrared"),
]

level_x_start = 1.0
level_x_end = 9.5

# Plot: each emission transition is a stem plus a filled arrowhead pointing down onto its lower level
HEAD_W, HEAD_H = 0.09, 0.42  # arrowhead half-width (x units) and length (y units), about 46 x 52 px
LABEL_FS = 36

levels = []
for y in visual_y.values():
    levels +=[(level_x_start, y), (level_x_end, y), None]

stems = {region: [] for region in REGIONS}
heads = []
wavelength_labels = []
for upper, lower, label, x, region in transitions:
    tip = visual_y[lower]
    stems[region] += [(x, visual_y[upper]), (x, tip + HEAD_H), None]
    # Closed triangle, first point repeated last, so pygal's fill closes it on itself
    heads.append((region, [(x - HEAD_W, tip + HEAD_H), (x, tip), (x + HEAD_W, tip + HEAD_H), (x - HEAD_W, tip + HEAD_H)]))
    wavelength_labels.append({"value": (x, visual_y[upper] + 0.32), "label": label})

region_labels = {}
for region in REGIONS:
    xs = [x for *_, x, r in transitions if r == region]
    region_labels[region] = [{"value": ((min(xs) + max(xs)) / 2, ionization_y + 0.55), "label": region}]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(
        *REGIONS.values(),  # region headers
        INK,  # wavelength labels
        INK_MUTED,  # level lines
        INK,  # ionization limit
        *REGIONS.values(),  # stems
        *(REGIONS[region] for region, _ in heads),
    ),
    value_colors=(*REGIONS.values(), INK_SOFT),
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=6,  # the transition stems; levels and the ionization line are set in the css below
    title_font_size=62,
    label_font_size=44,
    major_label_font_size=44,
    # pygal prints a point's label value_font_size px right of it and 4/3 of that below it;
    # at 0.26 x the label size the text sits vertically centred on its point
    value_font_size=round(0.26 * LABEL_FS),
    value_label_font_size=LABEL_FS,
    tooltip_font_size=34,
)

# pygal closes a fill down to the axis; with no stroke only the triangle itself shows
head_lines = ", ".join(f".serie-{9 + i} .line" for i in range(len(heads)))
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="Hydrogen Atom · energy-level-atomic · python · pygal · anyplot.ai",
    y_title="Energy (eV, levels evenly spaced)",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    margin=50,
    spacing=30,
    range=(0.4, 11),
    xrange=(0.6, 9.8),
    print_labels=True,
    print_values=False,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.text-overlay text.label { text-anchor: middle; }",
        "inline:.serie-0 text.label, .serie-1 text.label, .serie-2 text.label { font-size: 42px !important; font-weight: bold; }",
        "inline:.serie-4 .line, .serie-5 .line { stroke-width: 3px !important; }",
        f"inline:{head_lines} {{ stroke-width: 0 !important; }}",
        "inline:.plot_title { font-weight: bold; }",
    ),
)

# Y-axis labels showing quantum numbers and actual energy values
chart.y_labels = [{"label": f"n={n}:  {energy_ev[n]:.2f} eV".replace("-", "−"), "value": y} for n, y in visual_y.items()]
chart.y_labels += [{"label": "Ionization:  0.00 eV", "value": ionization_y}]

# Labels first, so their indices are fixed for the css above; text is always drawn above the marks
for region in REGIONS:
    chart.add(None, region_labels[region], stroke=False, dots_size=0)
chart.add(None, wavelength_labels, stroke=False, dots_size=0)
chart.add(None, levels, show_dots=False, allow_interruptions=True)
chart.add(
    None,
    [(level_x_start - 0.3, ionization_y), (level_x_end + 0.2, ionization_y)],
    show_dots=False,
    stroke_style={"dasharray": "18, 10"},
)
for region in REGIONS:
    chart.add(None, stems[region], show_dots=False, allow_interruptions=True)
for _, points in heads:
    chart.add(None, points, fill=True, show_dots=False)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
