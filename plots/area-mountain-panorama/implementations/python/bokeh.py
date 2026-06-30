"""anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: bokeh 3.9.0 | Python 3.14.4
"""

import os
import sys
import time
from pathlib import Path


# Remove script's own directory from sys.path to prevent self-shadowing
# (this file is named bokeh.py; without this, `import bokeh` would find itself)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import FixedTicker, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

# Data — Wallis (Valais, Switzerland) summit panorama, ordered W → E
peaks = [
    ("Weisshorn", 8, 4506),
    ("Zinalrothorn", 20, 4221),
    ("Ober Gabelhorn", 31, 4063),
    ("Dent Blanche", 42, 4358),
    ("Matterhorn", 58, 4478),
    ("Breithorn", 72, 4164),
    ("Pollux", 81, 4092),
    ("Castor", 89, 4223),
    ("Liskamm", 97, 4527),
    ("Dufourspitze", 109, 4634),
    ("Strahlhorn", 121, 4190),
    ("Rimpfischhorn", 132, 4199),
    ("Allalinhorn", 142, 4027),
    ("Alphubel", 152, 4206),
    ("Täschhorn", 162, 4491),
    ("Dom", 174, 4545),
]

# Build ridgeline control points: peaks alternating with saddles (cols)
np.random.seed(42)
ctrl_x = [-3.0]
ctrl_y = [3250.0]
for i, (_, ang, el) in enumerate(peaks):
    ctrl_x.append(float(ang))
    ctrl_y.append(float(el))
    if i < len(peaks) - 1:
        next_ang = peaks[i + 1][1]
        next_el = peaks[i + 1][2]
        col_ang = (ang + next_ang) / 2 + np.random.uniform(-1.2, 1.2)
        col_drop = np.random.uniform(420, 820)
        col_el = min(el, next_el) - col_drop
        ctrl_x.append(float(col_ang))
        ctrl_y.append(float(col_el))
ctrl_x.append(184.0)
ctrl_y.append(3350.0)
ctrl_x = np.array(ctrl_x)
ctrl_y = np.array(ctrl_y)

# Smooth ridgeline via cosine smoothstep between adjacent control points
ridge_x = []
ridge_y = []
for i in range(len(ctrl_x) - 1):
    n = 80
    last = i == len(ctrl_x) - 2
    t = np.linspace(0.0, 1.0, n, endpoint=last)
    s = 0.5 - 0.5 * np.cos(np.pi * t)
    ridge_x.append(ctrl_x[i] + (ctrl_x[i + 1] - ctrl_x[i]) * t)
    ridge_y.append(ctrl_y[i] + (ctrl_y[i + 1] - ctrl_y[i]) * s)
ridge_x = np.concatenate(ridge_x)
ridge_y = np.concatenate(ridge_y)

# Anchor the silhouette polygon at the lower edge of the visible y-range
Y_FLOOR = 2500
poly_x = np.concatenate([[ridge_x[0]], ridge_x, [ridge_x[-1]]])
poly_y = np.concatenate([[Y_FLOOR], ridge_y, [Y_FLOOR]])

# Assign label tiers avoiding same-tier collision for adjacent peaks
# Three tiers staggered vertically; greedy assignment per bearing proximity
LEVEL_TIERS = [4860, 5040, 5220]
tier_assignments = []
for i in range(len(peaks)):
    # Score each tier: avoid tier used by the immediately preceding peak
    prev_tier = tier_assignments[i - 1] if i > 0 else -1
    prev2_tier = tier_assignments[i - 2] if i > 1 else -1
    scores = []
    for t in range(3):
        penalty = 0
        if t == prev_tier:
            penalty += 2  # strong penalty for same tier as direct predecessor
        if t == prev2_tier:
            penalty += 1  # mild penalty for same tier as two peaks ago
        scores.append(penalty)
    tier_assignments.append(int(np.argmin(scores)))

# Canvas — hard rule: 3200×1800 landscape
W, H = 3200, 1800

p = figure(
    width=W,
    height=H,
    title="Wallis 4000ers · area-mountain-panorama · bokeh · anyplot.ai",
    y_axis_label="Elevation (m)",
    x_range=(-3, 184),
    y_range=(Y_FLOOR, 5600),
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    toolbar_location=None,  # disable toolbar — adds ~30-50px above canvas
    min_border_bottom=60,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Mountain silhouette — Imprint palette position 1 (brand green, always first series)
p.patch(poly_x, poly_y, fill_color=BRAND, line_color=BRAND, line_width=2)

# Peak labels with leader lines and summit dots
labels = []
for i, (name, ang, el) in enumerate(peaks):
    tier_idx = tier_assignments[i]
    label_y = LEVEL_TIERS[tier_idx]
    is_focal = name == "Matterhorn"
    leader_color = INK if is_focal else INK_SOFT
    leader_alpha = 0.9 if is_focal else 0.55
    leader_width = 3.0 if is_focal else 1.8

    # Leader line from just above summit to just below the label block
    p.line(
        [ang, ang], [el + 25, label_y - 90], line_color=leader_color, line_alpha=leader_alpha, line_width=leader_width
    )

    # Summit dot — larger and fully inked for the focal peak
    dot_size = 28 if is_focal else 20
    p.scatter([ang], [el], size=dot_size, fill_color=INK if is_focal else INK_SOFT, line_color=PAGE_BG, line_width=2)

    # Peak name label (top of stacked label block)
    labels.append(
        Label(
            x=ang,
            y=label_y + 55,
            text=name,
            text_color=INK,
            text_font_size="26pt" if is_focal else "21pt",
            text_font_style="bold" if is_focal else "normal",
            text_align="center",
            text_baseline="bottom",
        )
    )

    # Elevation label (below the name)
    labels.append(
        Label(
            x=ang,
            y=label_y + 30,
            text=f"{el:,} m",
            text_color=INK_SOFT,
            text_font_size="18pt",
            text_align="center",
            text_baseline="top",
        )
    )

# Matterhorn reference annotation — focal peak callout
labels.append(
    Label(
        x=58,
        y=4290,
        text="reference peak",
        text_color=INK_MUTED,
        text_font_size="16pt",
        text_font_style="italic",
        text_align="center",
        text_baseline="bottom",
    )
)

for lbl in labels:
    p.add_layout(lbl)

# Typography — per bokeh.md sizing for 3200×1800
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "normal"
p.title.align = "center"

p.yaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.yaxis.minor_tick_line_color = None
p.yaxis.ticker = FixedTicker(ticks=[2500, 3000, 3500, 4000, 4500, 5000])
p.yaxis.axis_label_standoff = 18

# Hide x-axis — bearing angles would clutter the panorama silhouette
p.xaxis.visible = False

# Grid: y-only, very subtle
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Save interactive HTML (required catalog artifact)
html_path = Path(f"plot-{THEME}.html")
output_file(str(html_path), title="Wallis 4000ers · area-mountain-panorama · bokeh · anyplot.ai")
save(p)

# Inject body background CSS to prevent thin border artifact in headless-Chrome screenshot
html_content = html_path.read_text()
body_style = f"<style>body{{margin:0;padding:0;background:{PAGE_BG};}}</style>"
html_content = html_content.replace("</head>", f"{body_style}\n</head>", 1)
html_path.write_text(html_content)

# Screenshot via headless Chrome — use CDP to set exact viewport to match figure dimensions
# (export_png uses a snap chromedriver that fails; set_window_size leaves ~140px gap)
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{html_path.resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
