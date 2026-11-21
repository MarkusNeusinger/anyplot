"""anyplot.ai
polar-line: Polar Line Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os
import sys


# Remove current directory from path to avoid importing this file as altair
cwd = os.getcwd()
if cwd in sys.path:
    sys.path.remove(cwd)
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: extra
THETA = "Angle (degrees)"  # role: theta
RADII = ["Northern City", "Southern City"]  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
north_temp = [5, 7, 12, 18, 24, 28, 30, 29, 24, 17, 10, 6]
south_temp = [28, 27, 24, 18, 12, 8, 7, 9, 14, 20, 24, 27]
df = pd.DataFrame(
    {
        MONTH: month_names,
        THETA: np.arange(len(month_names)) * 360 / len(month_names),
        RADII[0]: north_temp,
        RADII[1]: south_temp,
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
SIZE = 460  # inner view in px, square so the circles stay round


def to_xy(theta_deg, radius):
    """January at the top, months running clockwise."""
    rad = np.radians(theta_deg)
    return radius * np.sin(rad), radius * np.cos(rad)


# Close each series into a loop (cyclic data) and project to the plane
CITY = "City"
RADIUS = "Temperature (°C)"
long = df.melt(id_vars=[MONTH, THETA], value_vars=RADII, var_name=CITY, value_name=RADIUS)
series = [g.sort_values(THETA) for _, g in long.groupby(CITY, sort=False)]
lines = pd.concat([pd.concat([g, g.iloc[:1]]).assign(order=lambda t: np.arange(len(t))) for g in series])
lines["x"], lines["y"] = to_xy(lines[THETA], lines[RADIUS])

# Radius scale: round ring values derived from the data
step = 10 ** np.floor(np.log10(long[RADIUS].max()))
ring_values = np.arange(step, np.ceil(long[RADIUS].max() / step) * step + step / 2, step)
r_max = ring_values[-1]
lim = r_max * 1.28
dom = alt.Scale(domain=[-lim, lim], nice=False)

# Concentric rings
sweep = np.linspace(0, 360, 181)
rings = pd.concat(
    [
        pd.DataFrame(
            {"ring": f"{r:g}", "order": np.arange(len(sweep)), "x": to_xy(sweep, r)[0], "y": to_xy(sweep, r)[1]}
        )
        for r in ring_values
    ]
)

# Radial spokes and month labels
angles = long.drop_duplicates(THETA)[[THETA, MONTH]]
spoke_end = to_xy(angles[THETA], r_max)
spokes = pd.DataFrame({"x": 0.0, "y": 0.0, "x2": spoke_end[0], "y2": spoke_end[1]})
label_pos = to_xy(angles[THETA], r_max * 1.12)
month_labels = pd.DataFrame({"x": label_pos[0], "y": label_pos[1], "text": angles[MONTH]})

# Radius labels along the spoke halfway between the first two angles
tick_angle = angles[THETA].iloc[:2].mean()
tick_pos = to_xy(tick_angle, ring_values)
ring_labels = pd.DataFrame({"x": tick_pos[0], "y": tick_pos[1], "text": [f"{r:g}" for r in ring_values]})
unit = RADIUS[RADIUS.find("(") :] if "(" in RADIUS else ""
ring_labels.loc[ring_labels.index[-1], "text"] += f" {unit}".rstrip()

ring_layer = (
    alt.Chart(rings)
    .mark_line(strokeWidth=1, opacity=0.35, color=INK_SOFT)
    .encode(
        x=alt.X("x:Q", axis=None, scale=dom), y=alt.Y("y:Q", axis=None, scale=dom), detail="ring:N", order="order:Q"
    )
)
spoke_layer = (
    alt.Chart(spokes)
    .mark_rule(strokeWidth=1, opacity=0.3, color=INK_SOFT)
    .encode(x=alt.X("x:Q", scale=dom), y=alt.Y("y:Q", scale=dom), x2="x2:Q", y2="y2:Q")
)
month_layer = (
    alt.Chart(month_labels)
    .mark_text(fontSize=13, fontWeight="bold", color=INK)
    .encode(x=alt.X("x:Q", scale=dom), y=alt.Y("y:Q", scale=dom), text="text:N")
)
ring_label_layer = (
    alt.Chart(ring_labels)
    .mark_text(fontSize=11, color=INK_SOFT, align="left", dx=3, dy=-3)
    .encode(x=alt.X("x:Q", scale=dom), y=alt.Y("y:Q", scale=dom), text="text:N")
)

color = alt.Color(
    CITY.translate(ESCAPE),
    type="nominal",
    title=CITY,
    sort=None,
    scale=alt.Scale(range=IMPRINT_PALETTE),
    legend=alt.Legend(
        orient="bottom",
        direction="horizontal",
        titleFontSize=13,
        labelFontSize=12,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        titleColor=INK,
        labelColor=INK_SOFT,
        padding=6,
        symbolType="stroke",
        symbolStrokeWidth=3,
    ),
)
data_encoding = {
    "x": alt.X("x:Q", scale=dom),
    "y": alt.Y("y:Q", scale=dom),
    "color": color,
    "order": alt.Order("order:Q"),
    "tooltip": [
        alt.Tooltip(CITY.translate(ESCAPE), type="nominal", title=CITY),
        alt.Tooltip(MONTH.translate(ESCAPE), type="nominal", title=MONTH),
        alt.Tooltip(RADIUS.translate(ESCAPE), type="quantitative", title=RADIUS),
    ],
}
line_layer = alt.Chart(lines).mark_line(strokeWidth=3).encode(**data_encoding)
point_layer = alt.Chart(lines).mark_point(size=55, filled=True, opacity=1).encode(**data_encoding)

chart = (
    alt.layer(ring_layer, spoke_layer, ring_label_layer, line_layer, point_layer, month_layer)
    .properties(
        width=SIZE,
        height=SIZE,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title(
            text="Monthly Temperature · polar-line · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save, then pad (never crop) to the 2400 x 2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
