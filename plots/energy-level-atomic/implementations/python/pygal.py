""" anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 91/100 | Updated: 2026-11-08
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HC_EV_NM = 1239.84  # photon wavelength in nm = HC_EV_NM / photon energy in eV
IONIZATION_EV = 0.0  # energies are measured from the ionization limit
# Spectral regions in wavelength order, one Imprint hue each: blue on the short-wave side,
# green in the middle of the visible band, matte red on the long-wave side
REGIONS = [
    ("ultraviolet", 400, IMPRINT_PALETTE[2]),
    ("visible", 700, IMPRINT_PALETTE[0]),
    ("infrared", float("inf"), IMPRINT_PALETTE[4]),
]

# Columns: set these to your table's column names, one row per transition
LEVEL = "Level"  # role: level
ENERGY = "Energy (eV)"  # role: energy
LOWER_LEVEL = "Lower level"  # role: extra
LOWER_ENERGY = "Lower energy (eV)"  # role: extra
SERIES = "Series"  # role: transitions
LINE = "Line"  # role: extra

# Data: hydrogen emission lines, E(n) = −13.6 / n² eV; replace with e.g. df = pd.read_csv("lines.csv")
lines = [
    ("Lyman", "Ly-α", 2, 1),
    ("Lyman", "Ly-β", 3, 1),
    ("Lyman", "Ly-γ", 4, 1),
    ("Balmer", "Hα", 3, 2),
    ("Balmer", "Hβ", 4, 2),
    ("Balmer", "Hγ", 5, 2),
    ("Balmer", "Hδ", 6, 2),
    ("Paschen", "Pa-α", 4, 3),
    ("Paschen", "Pa-β", 5, 3),
    ("Paschen", "Pa-γ", 6, 3),
]
df = pd.DataFrame(
    {
        SERIES: [s for s, *_ in lines],
        LINE: [name for _, name, *_ in lines],
        LEVEL: [f"n={upper}" for *_, upper, _ in lines],
        ENERGY: [-13.6 / upper**2 for *_, upper, _ in lines],
        LOWER_LEVEL: [f"n={lower}" for *_, lower in lines],
        LOWER_ENERGY: [-13.6 / lower**2 for *_, lower in lines],
    }
)

# Plot: each emission transition is a stem plus a filled arrowhead pointing down onto its lower level
drawn = df.dropna(subset=[ENERGY, LOWER_ENERGY]).reset_index(drop=True)
levels_table = (
    pd.concat(
        [
            drawn[[LEVEL, ENERGY]].set_axis(["level", "energy"], axis=1),
            drawn[[LOWER_LEVEL, LOWER_ENERGY]].set_axis(["level", "energy"], axis=1),
        ]
    )
    .drop_duplicates("level")
    .sort_values("energy")
)

# Nonlinear axis: levels evenly spaced by rank, so the converging upper levels stay apart
LEVEL_STEP = 1.5
visual_y = {level: 1.0 + LEVEL_STEP * i for i, level in enumerate(levels_table["level"])}
energy_of = dict(zip(levels_table["level"], levels_table["energy"], strict=True))
ionization_y = 1.0 + LEVEL_STEP * len(visual_y)

# Schematic x: one column per series, arrows evenly spaced inside it
COLUMN_STEP, SERIES_GAP = 0.85, 0.3
series_names = drawn[SERIES].astype(str)
steps = COLUMN_STEP + SERIES_GAP * (series_names != series_names.shift())
steps.iloc[0] = 0
drawn["x"] = 1.8 + steps.cumsum()
level_x_start, level_x_end = 1.0, drawn["x"].max() + 0.4

region_bins = [0, *(upper_nm for _, upper_nm, _ in REGIONS)]
region_names = [name for name, *_ in REGIONS]
region_color = {name: color for name, _, color in REGIONS}
drawn["wavelength"] = HC_EV_NM / (drawn[ENERGY] - drawn[LOWER_ENERGY]).abs()
drawn["region"] = pd.cut(drawn["wavelength"], region_bins, labels=region_names).astype(str)
drawn["color"] = drawn["region"].map(region_color)

HEAD_W, HEAD_H = 0.09, 0.42  # arrowhead half-width (x units) and length (y units), about 46 x 52 px
LABEL_FS = 44

levels = []
for y in visual_y.values():
    levels += [(level_x_start, y), (level_x_end, y), None]

stem_colors = list(dict.fromkeys(drawn["color"]))
stems = {color: [] for color in stem_colors}
heads = []
wavelength_labels = []
for upper, lower, name, x, wavelength, color in zip(
    drawn[LEVEL], drawn[LOWER_LEVEL], drawn[LINE], drawn["x"], drawn["wavelength"], drawn["color"], strict=True
):
    start_y, tip = visual_y[upper], visual_y[lower]
    # The arrow runs from the first level to the second: down for emission, up for absorption
    base = tip + (HEAD_H if start_y >= tip else -HEAD_H)
    stems[color] += [(x, start_y), (x, base), None]
    # Closed triangle, first point repeated last, so pygal's fill closes it on itself
    heads.append((color, [(x - HEAD_W, base), (x, tip), (x + HEAD_W, base), (x - HEAD_W, base)]))
    wavelength_labels.append({"value": (x, max(start_y, tip) + 0.32), "label": f"{name} {wavelength:.0f} nm"})

# Each series header takes the spectral region most of its lines fall in
series_headers = []
for series, group in drawn.groupby(SERIES, sort=False):
    region = group["region"].mode().iloc[0]
    color = region_color[region]
    middle = (group["x"].min() + group["x"].max()) / 2
    series_headers.append((color, [{"value": (middle, ionization_y + 0.55), "label": f"{series} series · {region}"}]))

n_headers = len(series_headers)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(
        *(color for color, _ in series_headers),  # series headers
        INK,  # wavelength labels
        INK_MUTED,  # level lines
        INK,  # ionization limit
        *stem_colors,  # stems
        *(color for color, _ in heads),
    ),
    value_colors=(*(color for color, _ in series_headers), INK_SOFT),
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

# Series indices follow the add order below: headers, wavelength labels, levels, ionization, stems, heads
header_labels = ", ".join(f".serie-{i} text.label" for i in range(n_headers))
level_lines = f".serie-{n_headers + 1} .line, .serie-{n_headers + 2} .line"
first_head = n_headers + 3 + len(stem_colors)
# pygal closes a fill down to the axis; with no stroke only the triangle itself shows
head_lines = ", ".join(f".serie-{first_head + i} .line" for i in range(len(heads)))
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="Hydrogen Atom · energy-level-atomic · python · pygal · anyplot.ai",
    y_title=f"{ENERGY}, levels evenly spaced",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    margin=50,
    spacing=30,
    range=(0.4, ionization_y + 1.0),
    xrange=(level_x_start - 0.4, level_x_end + 0.3),
    print_labels=True,
    print_values=False,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.text-overlay text.label { text-anchor: middle; }",
        f"inline:{header_labels} {{ font-size: 42px !important; font-weight: bold; }}",
        f"inline:{level_lines} {{ stroke-width: 3px !important; }}",
        f"inline:{head_lines} {{ stroke-width: 0 !important; }}",
        "inline:.plot_title { font-weight: bold; }",
    ),
)

# Y-axis labels showing quantum numbers and actual energy values
chart.y_labels = [
    {"label": f"{level}:  {energy_of[level]:.2f} eV".replace("-", "−"), "value": y} for level, y in visual_y.items()
]
chart.y_labels += [{"label": f"Ionization:  {IONIZATION_EV:.2f} eV", "value": ionization_y}]

# Labels first, so their indices are fixed for the css above; text is always drawn above the marks
for _, header in series_headers:
    chart.add(None, header, stroke=False, dots_size=0)
chart.add(None, wavelength_labels, stroke=False, dots_size=0)
chart.add(None, levels, show_dots=False, allow_interruptions=True)
chart.add(
    None,
    [(level_x_start - 0.3, ionization_y), (level_x_end + 0.2, ionization_y)],
    show_dots=False,
    stroke_style={"dasharray": "18, 10"},
)
for color in stem_colors:
    chart.add(None, stems[color], show_dots=False, allow_interruptions=True)
for _, points in heads:
    chart.add(None, points, fill=True, show_dots=False)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
