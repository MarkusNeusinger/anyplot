"""anyplot.ai
violin-split: Split Violin Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-08
"""

import json
import os
import sys


# Remove script directory from path to avoid importing this file as altair
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != script_dir and p != ""]

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

# Imprint palette: all eight positions, one per split group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SCORE = "Score (%)"  # role: value
GROUP = "Group"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
# (control mean, control sd, treatment mean, treatment sd) per department
params = {
    "Engineering": (72, 12, 85, 10),
    "Marketing": (68, 15, 78, 12),
    "Sales": (75, 14, 80, 11),
    "HR": (70, 10, 76, 9),
}
rows = []
for dept, (c_mean, c_sd, t_mean, t_sd) in params.items():
    for group, mean, sd in (("Control", c_mean, c_sd), ("Treatment", t_mean, t_sd)):
        scores = np.clip(rng.normal(mean, sd, 100), 30, 100)
        rows.append(pd.DataFrame({DEPARTMENT: dept, SCORE: scores, GROUP: group}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
dept_f, score_f, group_f = (c.translate(ESCAPE) for c in (DEPARTMENT, SCORE, GROUP))
groups = list(df[GROUP].dropna().unique())
lo, hi = float(np.floor(df[SCORE].min())), float(np.ceil(df[SCORE].max()))
score_scale = alt.Scale(domain=[lo, hi])

# Facets wrap after four columns; the view height shrinks with the number of rows to stay on the canvas
FACET_COLUMNS = 4
facet_rows = -(-df[DEPARTMENT].nunique() // FACET_COLUMNS)
VIEW_W, VIEW_H = 125, max(30, 330 // facet_rows - 45)
half_gap = VIEW_W * 0.0625
offsets = np.linspace(-half_gap, half_gap, len(groups)).tolist()
group_scale = alt.Scale(domain=groups, range=IMPRINT_PALETTE)
offset_scale = alt.Scale(domain=groups, range=offsets)

# Quartiles per department and group, merged back for the inner markers
quartiles = (
    df.groupby([DEPARTMENT, GROUP], sort=False)[SCORE]
    .agg(median="median", q1=lambda x: x.quantile(0.25), q3=lambda x: x.quantile(0.75))
    .reset_index()
)
table = df.merge(quartiles, on=[DEPARTMENT, GROUP])

# Split violin: the first group's density goes left (negative), the others right
left_test = f"datum[{json.dumps(GROUP)}] === {json.dumps(str(groups[0]))}"
split_violin = (
    alt.Chart()
    .transform_density(density=score_f, as_=[SCORE, "density"], groupby=[DEPARTMENT, GROUP], extent=[lo, hi])
    .transform_calculate(signed_density=f"{left_test} ? -datum.density : datum.density")
    .mark_area(orient="horizontal", opacity=0.75)
    .encode(
        x=alt.X("signed_density:Q", title=None, axis=alt.Axis(labels=False, ticks=False, domain=False), stack=None),
        y=alt.Y(score_f, type="quantitative", title=SCORE, scale=score_scale),
        color=alt.Color(
            group_f,
            type="nominal",
            scale=group_scale,
            legend=alt.Legend(
                title=GROUP,
                titleFontSize=14,
                labelFontSize=13,
                symbolSize=200,
                orient="right",
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                titleColor=INK,
                labelColor=INK_SOFT,
            ),
        ),
    )
)

# IQR rule (vertical line from q1 to q3) at each group's side of the center
iqr_rule = (
    alt.Chart()
    .transform_aggregate(q1="min(q1)", q3="max(q3)", groupby=[DEPARTMENT, GROUP])
    .mark_rule(size=2.5, opacity=0.85)
    .encode(
        y=alt.Y("q1:Q", scale=score_scale),
        y2="q3:Q",
        xOffset=alt.XOffset(group_f, type="nominal", scale=offset_scale),
        color=alt.Color(group_f, type="nominal", scale=group_scale, legend=None),
    )
)

# Median as a white diamond with a group-colored outline
median_marker = (
    alt.Chart()
    .transform_aggregate(median="min(median)", groupby=[DEPARTMENT, GROUP])
    .mark_point(size=60, filled=True, shape="diamond", opacity=1)
    .encode(
        y=alt.Y("median:Q", scale=score_scale),
        xOffset=alt.XOffset(group_f, type="nominal", scale=offset_scale),
        color=alt.value("white"),
        stroke=alt.Color(group_f, type="nominal", scale=group_scale, legend=None),
        strokeWidth=alt.value(1.5),
    )
)

chart = (
    alt.layer(split_violin, iqr_rule, median_marker, data=table)
    .properties(width=VIEW_W, height=VIEW_H)
    .facet(
        facet=alt.Facet(
            dept_f, type="nominal", title=None, sort=None, header=alt.Header(labelFontSize=14, labelColor=INK)
        ),
        columns=FACET_COLUMNS,
    )
    .resolve_scale(x="independent")
    .properties(title=alt.Title("violin-split · python · altair · anyplot.ai", fontSize=18), background=PAGE_BG)
    .configure_facet(spacing=18)
    .configure_view(stroke=None, fill=PAGE_BG)
    .configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        titleColor=INK,
        labelColor=INK_SOFT,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
    )
    .configure_title(anchor="middle", offset=12, color=INK)
)

# Save (in script directory), padded up to the canonical landscape canvas
TW, TH = 3200, 1800
output_dir = os.path.dirname(os.path.abspath(__file__))
png_path = os.path.join(output_dir, f"plot-{THEME}.png")
chart.save(png_path, scale_factor=4.0)
img = Image.open(png_path).convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink the view size")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(png_path)
chart.save(os.path.join(output_dir, f"plot-{THEME}.html"))
