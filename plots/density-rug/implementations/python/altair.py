"""anyplot.ai
density-rug: Density Plot with Rug Marks
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-18
"""

import os
import sys


# Remove current directory from path IMMEDIATELY to avoid import shadowing
if sys.path[0] == "" or sys.path[0] == ".":
    sys.path.pop(0)
# Also remove the script directory if it's there
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single-series plot uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
RESPONSE_TIME = "Response time (ms)"  # role: values
DENSITY = "Density"  # computed below the Data block

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
response_times = np.concatenate(
    [
        rng.normal(150, 30, 80),  # most responses around 150 ms
        rng.normal(250, 40, 40),  # slower cluster around 250 ms
        rng.uniform(350, 500, 15),  # a few slow outliers
    ]
)
df = pd.DataFrame({RESPONSE_TIME: np.clip(response_times, 50, 500)})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
values = df[RESPONSE_TIME].dropna().to_numpy()

kde = gaussian_kde(values, bw_method=0.3)
grid = np.linspace(values.min() - 20, values.max() + 20, 300)
density_df = pd.DataFrame({RESPONSE_TIME: grid, DENSITY: kde(grid)})
top = density_df[DENSITY].max() * 1.08

# Rug ticks sit on the foot of the curve, centred half a tick above zero
TICK_PX = 16
view_height = 320
tick_height = top * TICK_PX / view_height
rug_df = pd.DataFrame({RESPONSE_TIME: values, "rug_y": tick_height / 2})

x_enc = alt.X(
    RESPONSE_TIME.translate(ESCAPE), type="quantitative", title=RESPONSE_TIME, scale=alt.Scale(nice=False, zero=False)
)
y_scale = alt.Scale(domain=[0, top], nice=False)

density_layer = (
    alt.Chart(density_df)
    .mark_area(opacity=0.35, color=BRAND, line={"color": BRAND, "strokeWidth": 2.5})
    .encode(x=x_enc, y=alt.Y(DENSITY, type="quantitative", title=DENSITY, scale=y_scale))
)

rug_layer = (
    alt.Chart(rug_df)
    .mark_tick(color=BRAND, opacity=0.5, thickness=1.5, size=TICK_PX)
    .encode(x=x_enc, y=alt.Y("rug_y", type="quantitative", scale=y_scale))
)

title = "density-rug · python · altair · anyplot.ai"
chart = (
    alt.layer(density_layer, rug_layer)
    .properties(
        width=620,
        height=view_height,
        background=PAGE_BG,
        title=alt.Title(title, fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
