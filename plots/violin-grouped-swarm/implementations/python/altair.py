"""anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-18
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
DODGE = 0.5  # distance between neighbouring group centres inside a category
VIOLIN_HALF_WIDTH = 0.21  # half width of the widest violin, in category-position units
JITTER = 0.09  # half width of the sideways swarm spread

# Columns: set these to your table's column names
TASK_TYPE = "Task type"  # role: category
EXPERTISE = "Expertise"  # role: group
RESPONSE_TIME = "Response time (s)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
tasks = {"Simple": 2.0, "Moderate": 4.5, "Complex": 8.0}
levels = {"Novice": (1.0, 1.5), "Expert": (0.6, 0.8)}
n_per_group = 40

rows = []
for task, task_mean in tasks.items():
    for level, (scale, spread) in levels.items():
        times = np.clip(rng.normal(task_mean * scale, spread, n_per_group), 0.5, 15)
        rows.append(pd.DataFrame({TASK_TYPE: task, EXPERTISE: level, RESPONSE_TIME: times}))
df = pd.concat(rows, ignore_index=True)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
task_order = list(df[TASK_TYPE].unique())
group_order = [str(group) for group in df[EXPERTISE].unique()]

# Dodged position of each group inside its category, centred on 0
df["position"] = (df[EXPERTISE].map({g: i for i, g in enumerate(group_order)}) - (len(group_order) - 1) / 2) * DODGE
df["swarm_x"] = df["position"] + np.random.default_rng(7).uniform(-JITTER, JITTER, len(df))

# Widest violin gets VIOLIN_HALF_WIDTH: scale every density by the tallest kernel density estimate
peak_density = max(
    gaussian_kde(values.dropna().to_numpy())(np.linspace(values.min(), values.max(), 200)).max()
    for _, values in df.groupby([TASK_TYPE, EXPERTISE])[RESPONSE_TIME]
)
violin_scale = VIOLIN_HALF_WIDTH / peak_density
half_span = df["position"].abs().max() + DODGE * 0.75

x_scale = alt.Scale(domain=[-half_span, half_span])
x_axis = alt.Axis(labels=False, ticks=False, grid=False, domain=False, title=None)
color = alt.Color(
    EXPERTISE.translate(ESCAPE),
    type="nominal",
    title=EXPERTISE,
    sort=group_order,
    scale=alt.Scale(domain=group_order, range=IMPRINT_PALETTE),
    legend=alt.Legend(titleFontSize=22, labelFontSize=20, symbolSize=500, offset=10),
)
y_enc = alt.Y(RESPONSE_TIME.translate(ESCAPE), type="quantitative", title=RESPONSE_TIME, axis=alt.Axis(grid=True))

violin = (
    alt.Chart()
    .transform_density(
        RESPONSE_TIME.translate(ESCAPE),
        as_=["value_axis", "density"],
        groupby=[TASK_TYPE.translate(ESCAPE), EXPERTISE.translate(ESCAPE), "position"],
    )
    .transform_calculate(
        left=f"datum.position - datum.density * {violin_scale}",
        right=f"datum.position + datum.density * {violin_scale}",
    )
    .mark_area(orient="horizontal", opacity=0.5, strokeWidth=2, stroke=None)
    .encode(
        x=alt.X("left:Q", scale=x_scale, axis=x_axis),
        x2="right:Q",
        y=alt.Y("value_axis:Q", title=RESPONSE_TIME, axis=alt.Axis(grid=True)),
        color=color,
    )
)

swarm = (
    alt.Chart()
    .mark_circle(opacity=0.9, size=110)
    .encode(
        x=alt.X("swarm_x:Q", scale=x_scale, axis=x_axis),
        y=y_enc,
        color=alt.Color(
            EXPERTISE.translate(ESCAPE),
            type="nominal",
            sort=group_order,
            scale=alt.Scale(domain=group_order, range=IMPRINT_PALETTE),
            legend=None,
        ),
    )
)

chart = (
    alt.layer(violin, swarm, data=df)
    .properties(width=185, height=305)
    .facet(
        column=alt.Column(
            TASK_TYPE.translate(ESCAPE),
            type="nominal",
            title=TASK_TYPE,
            sort=task_order,
            header=alt.Header(titleFontSize=24, labelFontSize=22, labelOrient="bottom"),
        ),
        spacing=14,
    )
    .properties(
        title=alt.Title(
            "violin-grouped-swarm · python · altair · anyplot.ai", fontSize=28, anchor="middle", offset=16, color=INK
        ),
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_header(labelColor=INK, titleColor=INK)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=10)
)

# Save: PNG padded (never cropped) to the 3200 x 1800 canvas, plus the interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    # Other data can widen the facets: shrink the whole picture to fit instead of cropping it
    fit = min(TARGET_W / img.width, TARGET_H / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.LANCZOS)
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
