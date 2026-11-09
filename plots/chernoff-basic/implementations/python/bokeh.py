""" anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, Range1d, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
EYE_WHITE = ELEVATED_BG if THEME == "light" else INK  # the eyes stay light with dark pupils in both themes
PUPIL = INK if THEME == "light" else PAGE_BG

# Imprint palette: one position per sector, in the order the sectors appear
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FEATURES = [  # driven by the variables in METRICS, in order
    "Face width",
    "Face height",
    "Eye size",
    "Mouth curve",
    "Brow slant",
    "Nose width",
]

# Columns: set these to your table's column names
COMPANY = "Company"  # role: observation_id
SECTOR = "Sector"  # role: extra
METRICS = [
    "Revenue Growth (%)",
    "Profit Margin (%)",
    "Customer Satisfaction (score)",
    "Market Share (%)",
    "Debt-to-Equity (ratio)",
    "R&D Spend (% of revenue)",
]  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("companies.csv")
np.random.seed(42)
profiles = {  # per sector: fictional companies and the plausible range of each metric, in its own unit
    "Tech": (
        ["Nimbus Systems", "Quantia Labs", "Corvex Software", "Helio Networks"],
        [(8, 35), (15, 30), (70, 88), (3, 20), (0.1, 0.6), (10, 25)],
    ),
    "Retail": (
        ["Marigold Stores", "Brightcart", "Urban Pantry", "Kestrel Outfitters"],
        [(-3, 10), (2, 8), (62, 85), (2, 12), (0.5, 1.5), (0.5, 3)],
    ),
    "Energy": (
        ["Northwind Power", "Basalt Petroleum", "Solvane Energy", "Ridgeline Utilities"],
        [(-5, 12), (5, 15), (55, 75), (4, 18), (0.8, 2.0), (1, 5)],
    ),
}
records = []
for sector, (names, ranges) in profiles.items():
    draws = np.column_stack([np.random.uniform(low, high, len(names)) for low, high in ranges])
    for name, row in zip(names, draws, strict=True):
        records.append({COMPANY: name, SECTOR: sector, **dict(zip(METRICS, row.round(2), strict=True))})
df = pd.DataFrame(records)

# Plot: reads only df and the constants above
W, H = 3200, 1800
MARGIN_SIDE, MARGIN_TOP, MARGIN_BOTTOM = 80, 230, 250  # the top band holds title and legend, the bottom one the key
FRAME_W, FRAME_H = W - 2 * MARGIN_SIDE, H - MARGIN_TOP - MARGIN_BOTTOM

# One palette position per sector; with more sectors than positions, all faces take the brand color and no legend
sectors = list(df[SECTOR].unique())
by_sector = len(sectors) <= len(IMPRINT_PALETTE)
colors = {sector: IMPRINT_PALETTE[i] if by_sector else IMPRINT_PALETTE[0] for i, sector in enumerate(sectors)}

# Each variable min-max scaled to 0-1, so every feature spans its full range
values = df[METRICS].astype(float)
span = (values.max() - values.min()).replace(0, 1)
scaled = ((values - values.min()) / span).to_numpy()
s_width, s_height, s_eye, s_mouth, s_brow, s_nose = scaled.T

# Grid: one cell per face, the y unit chosen so a data unit spans about the same pixels on both axes
n_faces = len(df)
n_cols = max(1, round(np.sqrt(n_faces * 4 / 3)))
n_rows = int(np.ceil(n_faces / n_cols))
cell_h = (FRAME_H / n_rows) / (FRAME_W / n_cols)
unit = min(1.0, cell_h)
col = np.arange(n_faces) % n_cols
row = np.arange(n_faces) // n_cols

faces = df.copy()
faces[[f"value_{i}" for i in range(len(METRICS))]] = values.to_numpy()  # positional copies for the hover template
faces["cx"] = col + 0.5
faces["cy"] = (n_rows - row - 0.5) * cell_h + 0.05 * unit
faces["rw"] = unit * (0.17 + 0.17 * s_width)
faces["rh"] = unit * (0.20 + 0.14 * s_height)
faces["w"] = 2 * faces["rw"]
faces["h"] = 2 * faces["rh"]
faces["eye_r"] = unit * (0.02 + 0.035 * s_eye)
faces["pupil_r"] = 0.45 * faces["eye_r"]
faces["eye_y"] = faces["cy"] + 0.2 * faces["rh"]
faces["eye_lx"] = faces["cx"] - 0.4 * faces["rw"]
faces["eye_rx"] = faces["cx"] + 0.4 * faces["rw"]
brow_y = faces["eye_y"] + faces["eye_r"] + 0.02 * unit  # sized so the brows stay inside the smallest face
brow_half = 0.9 * faces["eye_r"]
brow_tilt = unit * 0.045 * (s_brow - 0.5)  # a higher value lifts the outer ends into a frown
faces["brow_l_out"], faces["brow_l_in"] = faces["eye_lx"] - brow_half, faces["eye_lx"] + brow_half
faces["brow_r_in"], faces["brow_r_out"] = faces["eye_rx"] - brow_half, faces["eye_rx"] + brow_half
faces["brow_out_y"], faces["brow_in_y"] = brow_y + brow_tilt, brow_y - brow_tilt
faces["label_y"] = faces["cy"] - 0.36 * unit

# Nose: a wedge that widens as its variable rises; mouth: a parabola that frowns as its variable rises
nose_w = unit * (0.02 + 0.07 * s_nose)
nose_top = faces["cy"] + 0.02 * faces["rh"]
nose_tip = faces["cy"] - 0.2 * faces["rh"]
faces["nose_xs"] = list(np.column_stack([faces["cx"], faces["cx"] - nose_w / 2, faces["cx"] + nose_w / 2]))
faces["nose_ys"] = list(np.column_stack([nose_top, nose_tip, nose_tip]))
t = np.linspace(-1, 1, 25)
mouth_amp = (s_mouth - 0.5) * 0.5 * faces["rh"].to_numpy()
mouth_y = (faces["cy"] - 0.5 * faces["rh"]).to_numpy()
faces["mouth_xs"] = list(faces["cx"].to_numpy()[:, None] + 0.5 * faces["rw"].to_numpy()[:, None] * t)
faces["mouth_ys"] = list(mouth_y[:, None] + mouth_amp[:, None] * (1 - t**2))

title = "chernoff-basic · python · bokeh · anyplot.ai"
p = figure(
    width=W,
    height=H,
    title=title,
    x_range=Range1d(0, n_cols),
    y_range=Range1d(0, n_rows * cell_h),
    toolbar_location=None,
    min_border_left=MARGIN_SIDE,
    min_border_right=MARGIN_SIDE,
    min_border_top=MARGIN_TOP,
    min_border_bottom=MARGIN_BOTTOM,
)

# Faces, one renderer per sector so the legend follows the data's order
source = ColumnDataSource(faces)
face_renderers = {}
for sector, rows in faces.groupby(SECTOR, sort=False):
    face_renderers[sector] = p.ellipse(
        x="cx",
        y="cy",
        width="w",
        height="h",
        source=ColumnDataSource(rows),
        fill_color=colors[sector],
        fill_alpha=0.3,
        line_color=colors[sector],
        line_width=5,
    )

# Sector legend above the grid
legend = Legend(
    items=[LegendItem(label=str(sector), renderers=[r]) for sector, r in face_renderers.items()] if by_sector else [],
    orientation="horizontal",
    location="center",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    glyph_width=70,
    glyph_height=50,
    spacing=60,
    label_standoff=18,
    padding=10,
    margin=24,
    border_line_color=None,
    background_fill_alpha=0,
)
p.add_layout(legend, "above")

# Facial features, drawn for all faces at once
for eye_x in ("eye_lx", "eye_rx"):
    p.circle(x=eye_x, y="eye_y", radius="eye_r", source=source, fill_color=EYE_WHITE, line_color=INK, line_width=3)
    p.circle(x=eye_x, y="eye_y", radius="pupil_r", source=source, fill_color=PUPIL, line_color=None)
for side in ("l", "r"):
    p.segment(
        x0=f"brow_{side}_out",
        y0="brow_out_y",
        x1=f"brow_{side}_in",
        y1="brow_in_y",
        source=source,
        line_color=INK,
        line_width=5,
        line_cap="round",
    )
p.multi_line(xs="nose_xs", ys="nose_ys", source=source, line_color=INK, line_width=4, line_join="round")
p.multi_line(xs="mouth_xs", ys="mouth_ys", source=source, line_color=INK, line_width=5, line_cap="round")
p.text(
    x="cx",
    y="label_y",
    text=COMPANY,
    source=source,
    text_align="center",
    text_baseline="top",
    text_font_size="32pt",
    text_color=INK_SOFT,
)

# Key: which variable drives which feature, three entries per line, and in which direction
entries = [f"{feature}: {metric}" for feature, metric in zip(FEATURES, METRICS, strict=False)]
for start in range(0, len(entries), 3):
    p.add_layout(
        Title(
            text="   ·   ".join(entries[start : start + 3]),
            align="center",
            text_font_size="30pt",
            text_font_style="normal",
            text_color=INK,
            standoff=12,
        ),
        "below",
    )
p.add_layout(
    Title(
        text="Each variable min-max scaled across all faces: a higher value widens and lengthens the face, "
        "enlarges the eyes, turns the mouth down, slants the brows into a frown and widens the nose",
        align="center",
        text_font_size="26pt",
        text_font_style="italic",
        text_color=INK_SOFT,
        standoff=10,
    ),
    "below",
)

# Hover: the raw values behind each face
p.add_tools(
    HoverTool(
        renderers=list(face_renderers.values()),
        tooltips=[
            (COMPANY, f"@{{{COMPANY}}}"),
            (SECTOR, f"@{{{SECTOR}}}"),
            *[(metric, f"@value_{i}{{0.0[0]}}") for i, metric in enumerate(METRICS)],
        ],
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = PAGE_BG  # covers the page-white seam at the frame's edge
p.outline_line_width = 2
p.axis.visible = False
p.grid.visible = False

# Save: the interactive HTML, then a headless-Chrome screenshot of it at the exact canvas size
output_file(f"plot-{THEME}.html", title=title)
save(p)

opts = Options()
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", f"--window-size={W},{H}"):
    opts.add_argument(arg)
opts.add_argument("--hide-scrollbars")
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.execute_script("document.body.style.background = arguments[0]", PAGE_BG)  # no white hairline at the edges
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
