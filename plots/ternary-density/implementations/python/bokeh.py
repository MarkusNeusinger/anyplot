""" anyplot.ai
ternary-density: Ternary Density Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LinearColorMapper
from bokeh.plotting import figure
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: imprint_seq (brand green -> blue) as a 256-stop ramp for the density
SEQ_LOW, SEQ_HIGH = np.array([0x00, 0x9E, 0x73]), np.array([0x44, 0x67, 0xA3])
IMPRINT_SEQ256 = [
    "#{:02X}{:02X}{:02X}".format(*np.round(SEQ_LOW + (SEQ_HIGH - SEQ_LOW) * t).astype(int))
    for t in np.linspace(0, 1, 256)
]

# Columns: set these to your table's column names
SAND = "Sand"  # role: component_a
SILT = "Silt"  # role: component_b
CLAY = "Clay"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediments.csv")
np.random.seed(42)
# Sandy sediments (high sand)
sand1 = np.random.beta(5, 2, 200) * 80 + 10
silt1 = np.random.beta(2, 3, 200) * (100 - sand1) * 0.6
# Silty sediments (high silt)
silt2 = np.random.beta(5, 2, 150) * 70 + 20
sand2 = np.random.beta(2, 3, 150) * (100 - silt2) * 0.5
# Clayey sediments (high clay)
clay3 = np.random.beta(5, 2, 150) * 60 + 30
sand3 = np.random.beta(2, 3, 150) * (100 - clay3) * 0.4
df = pd.DataFrame(
    {
        SAND: np.concatenate([sand1, sand2, sand3]),
        SILT: np.concatenate([silt1, silt2, 100 - sand3 - clay3]),
        CLAY: np.concatenate([100 - sand1 - silt1, 100 - sand2 - silt2, clay3]),
    }
)

# Plot: reads only df and the constants above
H_TRI = np.sqrt(3) / 2
comp = df[[SAND, SILT, CLAY]].dropna()
comp = comp.div(comp.sum(axis=1), axis=0)  # closure: each composition sums to 1
x_data = comp[SILT] + comp[CLAY] / 2  # Sand at (0, 0), Silt at (1, 0), Clay at the apex
y_data = comp[CLAY] * H_TRI

# KDE on a grid, masked to the triangle (vectorized barycentric test)
grid_res = 300
xx, yy = np.meshgrid(np.linspace(0, 1, grid_res), np.linspace(0, H_TRI, grid_res))
inside = (yy <= np.sqrt(3) * xx + 1e-9) & (yy <= np.sqrt(3) * (1 - xx) + 1e-9)
kde = gaussian_kde(np.vstack([x_data, y_data]), bw_method="scott")
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
density = np.where(inside, density / density[inside].max(), np.nan)

p = figure(
    width=3200,
    height=1800,
    title="Sediment Composition · ternary-density · python · bokeh · anyplot.ai",
    x_range=(-0.32, 1.32),
    y_range=(-0.12, H_TRI + 0.1),
    match_aspect=True,
    tools="",
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=40,
    min_border_left=40,
    min_border_right=60,
)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.styles = {"background-color": PAGE_BG}  # page colour under the canvas hides the frame/border seam

color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=0, high=1, nan_color="rgba(0, 0, 0, 0)")
p.image(image=[density], x=0, y=0, dw=1, dh=H_TRI, color_mapper=color_mapper, alpha=0.9)

# Ternary grid at 10 % steps: one line per component level, each kept inside the triangle
levels = np.arange(1, 10) / 10
grid = pd.DataFrame(
    {
        "xs": [[f / 2, 1 - f / 2] for f in levels]  # constant Clay
        + [[f, (1 + f) / 2] for f in levels]  # constant Silt
        + [[1 - f, (1 - f) / 2] for f in levels],  # constant Sand
        "ys": [[f * H_TRI, f * H_TRI] for f in levels]
        + [[0, (1 - f) * H_TRI] for f in levels]
        + [[0, (1 - f) * H_TRI] for f in levels],
    }
)
p.multi_line(xs="xs", ys="ys", source=ColumnDataSource(grid), line_color=INK, line_alpha=0.28, line_width=2)
p.line([0, 1, 0.5, 0], [0, 0, H_TRI, 0], line_width=5, line_color=INK_SOFT)

# Vertex labels
for name, vx, vy, align, base in [
    (SAND, -0.03, -0.03, "right", "top"),
    (SILT, 1.03, -0.03, "left", "top"),
    (CLAY, 0.5, H_TRI + 0.03, "center", "bottom"),
]:
    p.add_layout(
        Label(
            x=vx,
            y=vy,
            text=name,
            text_font_size="44pt",
            text_font_style="bold",
            text_color=INK,
            text_align=align,
            text_baseline=base,
        )
    )

# Edge tick labels: Silt along the base, Clay up the right edge, Sand down the left edge
for f in [0.2, 0.4, 0.6, 0.8]:
    pct = f"{f * 100:.0f}%"
    for tx, ty, align, base in [
        (f, -0.025, "center", "top"),  # Silt share on the base
        (1 - f / 2 + 0.025, f * H_TRI, "left", "middle"),  # Clay share on the right edge
        ((1 - f) / 2 - 0.025, (1 - f) * H_TRI, "right", "middle"),  # Sand share on the left edge
    ]:
        p.add_layout(
            Label(
                x=tx, y=ty, text=pct, text_font_size="28pt", text_color=INK_SOFT, text_align=align, text_baseline=base
            )
        )

color_bar = ColorBar(
    color_mapper=color_mapper,
    width=50,
    title="Relative density",
    title_text_font_size="32pt",
    title_text_color=INK,
    title_text_font_style="normal",
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=None,
    bar_line_color=None,
    background_fill_color=PAGE_BG,
    title_standoff=20,
    padding=30,
)
p.add_layout(color_bar, "right")

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "normal"
p.title.align = "center"

# Save
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
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
