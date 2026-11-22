"""anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-20
"""

import sys
from pathlib import Path


_script_dir = str(Path(__file__).parent.absolute())
sys.path = [p for p in sys.path if p != _script_dir and p != ""]

import os  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool, Label  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
LOCUS_COLOR = IMPRINT_PALETTE[0]  # impedance locus
MARKER_COLOR = IMPRINT_PALETTE[1]  # matched condition and VSWR circle
BOUNDARY_COLOR = IMPRINT_PALETTE[2]  # unit circle and frequency labels

# Constants
Z0 = 50  # reference impedance in ohms
VSWR = 1.5  # reference circle drawn around the matched center
R_VALUES = [0.2, 0.5, 1, 2, 5]  # standard Smith chart grid: normalized resistance and reactance values

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
Z_REAL = "Resistance (Ω)"  # role: z_real
Z_IMAG = "Reactance (Ω)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
# Antenna S11 sweep 1-6 GHz: series RLC resonance at 3.5 GHz, Q=5
np.random.seed(42)
n_points = 60
freq = np.linspace(1e9, 6e9, n_points)
f_res = 3.5e9
Q = 5
R = 45 + 10 * np.exp(-((freq - f_res) ** 2) / (0.5e9) ** 2)
X = Z0 * Q * (freq / f_res - f_res / freq) + 5 * np.sin(2 * np.pi * freq / 2e9)
df = pd.DataFrame({FREQUENCY: freq, Z_REAL: R, Z_IMAG: X})

# Plot: reads only df and the constants above
z_norm = (df[Z_REAL] + 1j * df[Z_IMAG]) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
source = ColumnDataSource(
    {"gr": np.real(gamma), "gi": np.imag(gamma), "ghz": df[FREQUENCY] / 1e9, "r": df[Z_REAL], "x": df[Z_IMAG]}
)

# Canvas: 2400x2400 (square, symmetric Smith chart)
W, H = 2400, 2400
extent = 1.35  # the unit circle plus room for the grid labels

p = figure(
    width=W,
    height=H,
    title="smith-chart-basic · python · bokeh · anyplot.ai",
    x_range=(-extent, extent),
    y_range=(-extent, extent),
    match_aspect=True,
    toolbar_location=None,
    min_border_bottom=60,
    min_border_left=60,
    min_border_top=110,
    min_border_right=60,
)

# Theme-adaptive chrome: the Smith grid replaces the Cartesian axes
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = PAGE_BG
p.axis.visible = False
p.grid.visible = False

# Unit circle: outer boundary |Γ| = 1
theta = np.linspace(0, 2 * np.pi, 500)
p.line(np.cos(theta), np.sin(theta), line_width=4, line_color=BOUNDARY_COLOR, alpha=0.9)

# Constant resistance circles
th = np.linspace(0, 2 * np.pi, 400)
for r in R_VALUES:
    center = r / (1 + r)
    radius = 1 / (1 + r)
    p.line(center + radius * np.cos(th), radius * np.sin(th), line_width=1.5, line_color=INK_SOFT, alpha=0.30)

# Constant reactance arcs, clipped to the unit circle
th = np.linspace(-np.pi, np.pi, 600)
for x in R_VALUES:
    for sign in [1, -1]:
        radius = 1.0 / x
        cy_center = sign * radius
        ax = 1.0 + radius * np.cos(th)
        ay = cy_center + radius * np.sin(th)
        mask = (ax**2 + ay**2 <= 1.001) & (ax >= -0.001)
        ax_m, ay_m = ax[mask], ay[mask]
        if len(ax_m) > 1:
            order = np.argsort(np.arctan2(ay_m - cy_center, ax_m - 1.0))
            p.line(ax_m[order], ay_m[order], line_width=1.5, line_color=INK_SOFT, alpha=0.30)

# Pure-resistance axis (x = 0)
p.line([-1, 1], [0, 0], line_width=2, line_color=INK_SOFT, alpha=0.5)

# VSWR reference circle: constant |Γ|
vswr_r = (VSWR - 1) / (VSWR + 1)
p.ellipse(
    x=0,
    y=0,
    width=2 * vswr_r,
    height=2 * vswr_r,
    fill_color=MARKER_COLOR,
    fill_alpha=0.08,
    line_color=MARKER_COLOR,
    line_dash="dashed",
    line_width=2.5,
    line_alpha=0.60,
)

# Hover readout in the interactive HTML
p.add_tools(
    HoverTool(
        tooltips=[
            ("Frequency", "@ghz{0.2f} GHz"),
            ("R", "@r{0.1f} Ω"),
            ("X", "@x{+0.1f} Ω"),
            ("Γ", "(@gr{0.3f}, @gi{+0.3f}j)"),
        ]
    )
)

# Impedance locus
p.line("gr", "gi", source=source, line_width=5, line_color=LOCUS_COLOR, alpha=0.9)
p.scatter("gr", "gi", source=source, size=14, fill_color=LOCUS_COLOR, line_color=PAGE_BG, line_width=2, alpha=0.85)

# Frequency labels at key points, pushed outward from the chart center in screen pixels
label_indices = [0, len(df) // 4, len(df) // 2, 3 * len(df) // 4, len(df) - 1]
for idx in label_indices:
    gx, gy = gamma.iloc[idx].real, gamma.iloc[idx].imag
    norm = max(np.hypot(gx, gy), 1e-9)
    dx, dy = 90 * gx / norm, 90 * gy / norm  # outward from the chart center, screen pixels (y up)
    p.add_layout(
        Label(
            x=gx,
            y=gy,
            x_offset=int(dx),
            y_offset=int(dy),
            text_align="center",
            text_baseline="middle",
            text=f"{df[FREQUENCY].iloc[idx] / 1e9:.1f} GHz",
            text_font_size="26pt",
            text_color=BOUNDARY_COLOR,
            text_font_style="bold",
        )
    )

# Matched condition marker: Γ = 0 (Z = Z₀)
p.scatter([0], [0], size=24, fill_color=MARKER_COLOR, line_color=PAGE_BG, line_width=3)
p.add_layout(
    Label(
        x=0,
        y=0,
        x_offset=-24,
        y_offset=24,
        text_align="right",
        text="Z=Z₀",
        text_font_size="26pt",
        text_color=MARKER_COLOR,
        text_font_style="bold",
    )
)
p.add_layout(
    Label(
        x=vswr_r * np.cos(np.pi / 4),
        y=vswr_r * np.sin(np.pi / 4),
        x_offset=8,
        y_offset=8,
        text=f"VSWR={VSWR}",
        text_font_size="20pt",
        text_color=MARKER_COLOR,
        text_font_style="italic",
    )
)

# Normalized resistance labels below the horizontal axis, one per circle
for r in R_VALUES[:4]:
    p.add_layout(
        Label(
            x=r / (1 + r),
            y=0,
            y_offset=-48,
            text=f"r={r}",
            text_font_size="22pt",
            text_color=INK_MUTED,
            text_align="center",
        )
    )

# Normalized reactance labels where each arc meets the boundary
for x in R_VALUES[1:4]:
    angle = 2 * np.arctan(1 / x)
    lx, ly = np.cos(angle), np.sin(angle)
    p.add_layout(Label(x=lx, y=ly, x_offset=10, y_offset=6, text=f"x={x}", text_font_size="20pt", text_color=INK_MUTED))
    p.add_layout(
        Label(x=lx, y=-ly, x_offset=10, y_offset=-36, text=f"x=−{x}", text_font_size="20pt", text_color=INK_MUTED)
    )

# Save interactive HTML
output_file(f"plot-{THEME}.html", title="Smith Chart – python – bokeh – anyplot.ai")
save(p)

# Screenshot with headless Chrome (Selenium)
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
