"""anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColumnDataSource, HoverTool, Label, NormalHead, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Spectral region of a transition: (upper wavelength bound in nm, Imprint color), shortest first
SPECTRAL_COLORS = [
    (400, IMPRINT_PALETTE[1]),  # ultraviolet
    (450, IMPRINT_PALETTE[1]),  # violet, the lighter Imprint violet stays legible on the dark page
    (495, IMPRINT_PALETTE[2]),  # blue
    (700, IMPRINT_PALETTE[4]),  # red end of the visible range
    (float("inf"), IMPRINT_PALETTE[3]),  # infrared
]
TICK_STEPS = [0.5, 1.0, 5.0, 10.0]  # round energies (eV) marked on the compressed axis, besides the lowest levels
IONIZATION_ENERGY = 0.0  # energy of the free electron (eV)

# Columns: one row per emission transition
LEVEL = "Upper level n"  # role: level
ENERGY = "Energy (eV)"  # role: energy
LOWER_LEVEL = "Lower level n"  # role: extra
LOWER_ENERGY = "Lower energy (eV)"  # role: extra
LINE = "Line"  # role: extra
WAVELENGTH = "Wavelength (nm)"  # role: extra
SERIES = "Series"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("transitions.csv")
# Hydrogen atom, E_n = -13.6 / n² eV; one row per transition from an upper to a lower level
lines = [
    ("Lyman (UV)", 2, 1, "Lyα", 121.6),
    ("Lyman (UV)", 3, 1, "Lyβ", 102.6),
    ("Lyman (UV)", 4, 1, "Lyγ", 97.3),
    ("Balmer (Visible)", 3, 2, "Hα", 656.3),
    ("Balmer (Visible)", 4, 2, "Hβ", 486.1),
    ("Balmer (Visible)", 5, 2, "Hγ", 434.0),
    ("Balmer (Visible)", 6, 2, "Hδ", 410.2),
    ("Paschen (IR)", 4, 3, "Paα", 1875.0),
    ("Paschen (IR)", 5, 3, "Paβ", 1282.0),
    ("Paschen (IR)", 6, 3, "Paγ", 1094.0),
]
df = pd.DataFrame(lines, columns=[SERIES, LEVEL, LOWER_LEVEL, LINE, WAVELENGTH])
df[ENERGY] = -13.6 / df[LEVEL] ** 2
df[LOWER_ENERGY] = -13.6 / df[LOWER_LEVEL] ** 2

# Plot
W, H = 3200, 1800

# Levels seen anywhere in the transitions, ordered from the ground state up
levels = (
    pd.concat(
        [
            df[[LEVEL, ENERGY]].set_axis(["n", "energy"], axis=1),
            df[[LOWER_LEVEL, LOWER_ENERGY]].set_axis(["n", "energy"], axis=1),
        ]
    )
    .drop_duplicates("n")
    .sort_values("n")
    .reset_index(drop=True)
)

# Square-root compression pulls the converging upper levels apart: visual y = -sqrt(|E|)
levels["vy"] = -np.sqrt(np.abs(levels["energy"] - IONIZATION_ENERGY))
vy_of = dict(zip(levels["n"], levels["vy"], strict=True))
span = -levels["vy"].min()
y_low, y_high = levels["vy"].min() - 0.08 * span, 0.22 * span

# Horizontal layout: the first series sits left of the level lines, the others to their right
level_x0, level_x1 = -1.5, 1.5
arrow_spacing = 0.55
series_names = list(df[SERIES].unique())
x_cursor = {series_names[0]: -3.5}
x_next = 3.2
for name in series_names[1:]:
    x_cursor[name] = x_next
    x_next += (df[SERIES] == name).sum() * arrow_spacing + 0.3
x_min = x_cursor[series_names[0]] - 1.5
x_max = x_next + 0.9

# Ticks of the compressed axis: ground levels plus round energies inside the range
low_energy = levels["energy"].min()
tick_energies = sorted(
    {IONIZATION_ENERGY, *levels["energy"].iloc[:3], *(-s for s in TICK_STEPS if s < abs(low_energy))}, reverse=True
)
tick_visual = [-np.sqrt(abs(e - IONIZATION_ENERGY)) for e in tick_energies]
tick_labels = [f"{e:.1f}" for e in tick_energies]

level_source = ColumnDataSource(
    data={
        "x0": [level_x0] * len(levels),
        "y0": levels["vy"],
        "x1": [level_x1] * len(levels),
        "y1": levels["vy"],
        "quantum_n": [f"n = {n}" for n in levels["n"]],
        "energy": [f"{e:.2f} eV" for e in levels["energy"]],
        "degeneracy": [f"{n**2}-fold" for n in levels["n"]],
    }
)

p = figure(
    width=W,
    height=H,
    title="energy-level-atomic · python · bokeh · anyplot.ai",
    x_range=Range1d(x_min, x_max),
    y_range=Range1d(y_low, y_high),
    toolbar_location=None,
    min_border_bottom=100,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.yaxis.ticker = tick_visual
p.yaxis.major_label_overrides = dict(zip(tick_visual, tick_labels, strict=True))
p.yaxis.axis_label = ENERGY

# Energy level lines in the first Imprint color
level_glyph = p.segment(
    x0="x0", y0="y0", x1="x1", y1="y1", source=level_source, line_width=8, line_color=IMPRINT_PALETTE[0]
)
p.add_tools(
    HoverTool(
        renderers=[level_glyph],
        tooltips=[("Level", "@quantum_n"), ("Energy", "@energy"), ("Degeneracy", "@degeneracy")],
    )
)

# Faint level guides under the arrow columns, so each arrow starts and ends on its level;
# the stretch under the level labels stays free
guide_left = (x_cursor[series_names[0]] - 0.3, level_x0)
guide_right = (level_x1 + 1.5, x_next - 0.4)
for gx0, gx1 in (guide_left, guide_right):
    p.segment(
        x0=[gx0] * len(levels),
        y0=levels["vy"],
        x1=[gx1] * len(levels),
        y1=levels["vy"],
        line_width=3,
        line_color=IMPRINT_PALETTE[0],
        line_alpha=0.4,
    )

# Level labels right of the level lines
for n, e, vy in zip(levels["n"], levels["energy"], levels["vy"], strict=True):
    p.add_layout(
        Label(
            x=level_x1 + 0.15,
            y=vy,
            text=f"n={n}  ({e:.2f} eV)",
            text_font_size="22pt",
            text_color=INK_SOFT,
            text_baseline="middle",
        )
    )

# Ionization limit: dashed line across the plot, labeled
p.segment(x0=[x_min], y0=[0.0], x1=[x_max], y1=[0.0], line_width=3, line_color=INK_MUTED, line_dash="dashed")
p.add_layout(
    Label(
        x=level_x1 + 0.15,
        y=0.03 * span,
        text=f"Ionization ({IONIZATION_ENERGY:g} eV)",
        text_font_size="22pt",
        text_color=INK_MUTED,
    )
)

# Transition arrows colored by spectral region, labeled with their wavelength
for series_name, group in df.groupby(SERIES, sort=False):
    x_start = x_cursor[series_name]
    on_left = series_name == series_names[0]
    first_color = None
    for i, row in enumerate(group.itertuples(index=False)):
        wavelength = row[4]
        color = next((c for bound, c in SPECTRAL_COLORS if wavelength < bound), INK_MUTED)
        first_color = first_color or color
        y_from, y_to = vy_of[row[1]], vy_of[row[2]]
        x_pos = x_start + i * arrow_spacing
        p.add_layout(
            Arrow(
                end=NormalHead(size=22, fill_color=color, line_color=color),
                x_start=x_pos,
                y_start=y_from,
                x_end=x_pos,
                y_end=y_to,
                line_color=color,
                line_width=4,
            )
        )
        p.add_layout(
            Label(
                x=x_pos,
                y=(y_from + y_to) / 2,
                text=f"{row[3]} {wavelength:g} nm",
                text_font_size="20pt",
                text_color=color,
                text_align="center",
                text_baseline="bottom",
                angle=np.pi / 2,
                x_offset=-8,
            )
        )
    centre = x_start + (len(group) - 1) / 2 * arrow_spacing
    p.add_layout(
        Label(
            x=centre,
            y=0.157 * span,
            text=f"{series_name} series",
            text_font_size="26pt",
            text_font_style="bold",
            text_color=first_color,
            text_align="center",
        )
    )

# Style (theme-adaptive chrome)
p.title.text_font_size = "50pt"
p.title.text_font_style = "normal"
p.title.text_color = INK

p.yaxis.axis_label_text_font_size = "42pt"
p.yaxis.major_label_text_font_size = "34pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xaxis.visible = False
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save
output_file(f"plot-{THEME}.html", title="Atomic Energy Level Diagram")
save(p)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager)
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
# Force the viewport to exactly W×H via CDP: the window chrome otherwise shrinks it
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
# Paint the page in the theme color so the anti-aliased canvas edge shows no white line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
