"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
VIOLIN_HALF_WIDTH = 0.4  # widest half-width of a violin, in category-axis units
BANDWIDTH = 0.3  # KDE bandwidth factor
POINT_SIZE = 40  # marker area in px^2 on the 620 x 320 view
VIEW_W, VIEW_H = 620, 320

# Columns: set these to your table's column names
CONDITION = "Condition"  # role: category
REACTION = "Reaction time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("reaction_times.csv")
np.random.seed(42)
n_per_group = 50
df = pd.DataFrame(
    {
        CONDITION: np.repeat(["Condition A", "Condition B", "Condition C", "Condition D"], n_per_group),
        REACTION: np.concatenate(
            [
                np.random.normal(320, 40, n_per_group),  # roughly normal
                np.random.gamma(8, 30, n_per_group) + 200,  # right-skewed
                np.concatenate(
                    [np.random.normal(280, 25, n_per_group // 2), np.random.normal(380, 30, n_per_group // 2)]
                ),  # bimodal
                np.random.normal(400, 25, n_per_group),  # higher mean, tight spread
            ]
        ),
    }
)

# Plot: reads only df and the constants above
df = df.dropna(subset=[CONDITION, REACTION])
groups = list(dict.fromkeys(df[CONDITION]))
n_groups = len(groups)
colors = {g: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, g in enumerate(groups)}

x_domain = [-0.6, n_groups - 0.4]
v_min, v_max = df[REACTION].min(), df[REACTION].max()
pad = (v_max - v_min) * 0.12
y_domain = [v_min - pad, v_max + pad]
px_per_x = VIEW_W / (x_domain[1] - x_domain[0])
px_per_y = VIEW_H / (y_domain[1] - y_domain[0])

# Violin outlines: a KDE per group, evaluated only slightly beyond its own data range
violin_rows = []
for i, g in enumerate(groups):
    vals = df.loc[df[CONDITION] == g, REACTION].to_numpy()
    if len(vals) < 2 or np.ptp(vals) == 0:
        continue
    kde = stats.gaussian_kde(vals, bw_method=BANDWIDTH)
    cut = kde.factor * vals.std(ddof=1)
    grid = np.linspace(vals.min() - cut, vals.max() + cut, 120)
    half = kde(grid) / kde(grid).max() * VIOLIN_HALF_WIDTH
    violin_rows.append(pd.DataFrame({"group": g, "y": grid, "x_left": i - half, "x_right": i + half}))
violin_df = pd.concat(violin_rows, ignore_index=True)

# Swarm layout: each point, in value order, takes the smallest sideways offset that keeps it
# one marker diameter away from the points already placed (offsets are layout; values stay put)
diameter = 1.15 * np.sqrt(4 * POINT_SIZE / np.pi)
point_rows = []
for i, g in enumerate(groups):
    vals = np.sort(df.loc[df[CONDITION] == g, REACTION].to_numpy())
    placed = []
    for v in vals:
        y_px = v * px_per_y
        candidates = [0.0]
        for ox, oy in placed:
            if abs(oy - y_px) < diameter:
                shift = np.sqrt(diameter**2 - (oy - y_px) ** 2)
                candidates += [ox + shift, ox - shift]
        for c in sorted(candidates, key=abs):
            if all((c - ox) ** 2 + (y_px - oy) ** 2 >= diameter**2 - 1e-6 for ox, oy in placed):
                break
        placed.append((c, y_px))
        point_rows.append({"group": g, "y": v, "x": i + c / px_per_x})
points_df = pd.DataFrame(point_rows)

x_axis = alt.Axis(
    values=list(range(n_groups)),
    labelExpr=f"{groups!r}[datum.value]",
    labelFontSize=10,
    labelPadding=6,
    grid=False,
    ticks=False,
    title=CONDITION,
    titleFontSize=12,
)
y_axis = alt.Axis(labelFontSize=10, titleFontSize=12, title=REACTION, grid=True, gridOpacity=0.12)
color = alt.Color("group:N", scale=alt.Scale(domain=groups, range=[colors[g] for g in groups]), legend=None, sort=None)
x_scale = alt.Scale(domain=x_domain, nice=False)
y_scale = alt.Scale(domain=y_domain, nice=False, zero=False)

violin = (
    alt.Chart(violin_df)
    .mark_area(opacity=0.4, orient="horizontal", interpolate="monotone")
    .encode(
        y=alt.Y("y:Q", scale=y_scale, axis=y_axis),
        x=alt.X("x_left:Q", scale=x_scale, axis=x_axis),
        x2="x_right:Q",
        color=color,
        detail="group:N",
    )
)

swarm = (
    alt.Chart(points_df)
    .mark_circle(size=POINT_SIZE, clip=True, opacity=0.9, stroke=PAGE_BG, strokeWidth=0.5)
    .encode(
        y=alt.Y("y:Q", scale=y_scale, axis=y_axis),
        x=alt.X("x:Q", scale=x_scale, axis=x_axis),
        color=color,
        tooltip=[alt.Tooltip("group:N", title=CONDITION), alt.Tooltip("y:Q", title=REACTION, format=".1f")],
    )
)

title = "violin-swarm · python · altair · anyplot.ai"
chart = (
    alt.layer(violin, swarm)
    .properties(
        width=VIEW_W, height=VIEW_H, background=PAGE_BG, title=alt.Title(title, fontSize=16, anchor="middle", color=INK)
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, labelColor=INK_SOFT, titleColor=INK)
)

# Save: pad (never crop) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
