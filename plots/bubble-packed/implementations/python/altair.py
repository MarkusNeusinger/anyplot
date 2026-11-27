"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 8 hues, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LABEL_SHARE = 0.25  # circles below this share of the radius range carry their name only

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: label
BUDGET = "Budget ($K)"  # role: value
DIVISION = "Division"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("budgets.csv")
df = pd.DataFrame(
    {
        DEPARTMENT: [
            "Engineering",
            "R&D",
            "Data Science",
            "QA",
            "Marketing",
            "Sales",
            "Support",
            "Operations",
            "IT",
            "Security",
            "Finance",
            "HR",
            "Legal",
            "Design",
            "Product",
        ],
        BUDGET: [850, 750, 460, 195, 420, 680, 210, 320, 380, 170, 290, 180, 150, 240, 550],
        DIVISION: ["Technology"] * 4 + ["Revenue"] * 3 + ["Operations"] * 3 + ["Corporate"] * 3 + ["Product"] * 2,
    }
)

# Plot: reads only df and the constants above
# Circle packing: the area of each circle is proportional to its value. Largest first, each circle goes
# where it touches two placed circles, overlaps none, and sits closest to the centre of what is placed.
radius = np.sqrt(df[BUDGET].to_numpy(dtype=float))
centers = np.zeros((len(df), 2))
placed = []
for i in np.argsort(-radius, kind="stable"):
    if not placed:
        placed.append(i)
        continue
    if len(placed) == 1:
        centers[i] = centers[placed[0]] + [radius[placed[0]] + radius[i], 0.0]
        placed.append(i)
        continue
    weights = radius[placed] ** 2
    middle = (centers[placed] * weights[:, None]).sum(axis=0) / weights.sum()
    best, best_dist = None, np.inf
    for a_pos, a in enumerate(placed):
        for b in placed[a_pos + 1 :]:
            d = np.linalg.norm(centers[b] - centers[a])
            ra, rb = radius[a] + radius[i], radius[b] + radius[i]
            if d > ra + rb or d < abs(ra - rb):
                continue
            along = (ra**2 - rb**2 + d**2) / (2 * d)
            height = np.sqrt(max(ra**2 - along**2, 0.0))
            unit = (centers[b] - centers[a]) / d
            for sign in (1, -1):
                spot = centers[a] + unit * along + sign * height * np.array([-unit[1], unit[0]])
                gaps = np.linalg.norm(centers[placed] - spot, axis=1) - radius[placed] - radius[i]
                if gaps.min() > -1e-9 and np.linalg.norm(spot - middle) < best_dist:
                    best, best_dist = spot, np.linalg.norm(spot - middle)
    centers[i] = best
    placed.append(i)

# Centre on the area-weighted middle and scale the enclosing circle to radius 1
centers -= (centers * radius[:, None] ** 2).sum(axis=0) / (radius**2).sum()
enclosing = (np.linalg.norm(centers, axis=1) + radius).max()
df["x"], df["y"], df["r"] = centers[:, 0] / enclosing, centers[:, 1] / enclosing, radius / enclosing

# The chart is fitted to 600 x 600, so the view is a little shorter than wide; one scale for both axes
# keeps the packed circles round and touching (view size measured from the fitted chart)
VIEW_W, VIEW_H = 580, 548
px_per_unit = min(VIEW_W, VIEW_H) / 2.3
half_w, half_h = VIEW_W / 2 / px_per_unit, VIEW_H / 2 / px_per_unit

df["area_px"] = (2 * df["r"] * px_per_unit) ** 2  # Vega draws a circle with diameter sqrt(size)
df["budget_text"] = "$" + df[BUDGET].astype(str) + "K"
radius_cut = df["r"].min() + (df["r"].max() - df["r"].min()) * LABEL_SHARE
df["caption"] = np.where(df["r"] >= radius_cut, df[DEPARTMENT] + "\n" + df["budget_text"], df[DEPARTMENT])

divisions = df[DIVISION].unique()
colors = dict(zip(divisions, IMPRINT_PALETTE, strict=False))

# Label color follows the fill: dark ink on light fills (lavender), white on dark ones
rgb = np.array([[int(colors[d][i : i + 2], 16) / 255 for i in (1, 3, 5)] for d in df[DIVISION]])
linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
luminance = linear @ np.array([0.2126, 0.7152, 0.0722])
# WCAG contrast of white (1.05 / (L + 0.05)) against dark ink (L_ink ≈ 0.01)
df["label_color"] = np.where(1.05 / (luminance + 0.05) >= (luminance + 0.05) / 0.06, "#FFFFFF", "#1A1A17")

ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
DEPARTMENT_F, BUDGET_F, DIVISION_F = (c.translate(ESCAPE) for c in (DEPARTMENT, BUDGET, DIVISION))

# Interactive legend selection — click a division to highlight it
selection = alt.selection_point(fields=[DIVISION_F], bind="legend")

x_axis = alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-half_w, half_w], nice=False))
y_axis = alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-half_h, half_h], nice=False))

circles_layer = (
    alt.Chart(df)
    .mark_circle(stroke=PAGE_BG, strokeWidth=2.5)
    .encode(
        x=x_axis,
        y=y_axis,
        size=alt.Size("area_px:Q", scale=None, legend=None),
        color=alt.Color(
            DIVISION_F,
            type="nominal",
            title=DIVISION,
            sort=None,
            scale=alt.Scale(domain=list(colors), range=list(colors.values())),
            legend=alt.Legend(
                titleFontSize=12, titleFontWeight="bold", labelFontSize=11, symbolSize=240, orient="top-left", padding=6
            ),
        ),
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip(DEPARTMENT_F, type="nominal", title=DEPARTMENT),
            alt.Tooltip(BUDGET_F, type="quantitative", title=BUDGET),
            alt.Tooltip(DIVISION_F, type="nominal", title=DIVISION),
        ],
    )
    .add_params(selection)
)

# Labels inside the circles: name + budget in the large ones, name only in the small ones
captions = (
    alt.Chart(df)
    .mark_text(fontWeight="bold", lineBreak="\n")
    .encode(
        x=x_axis,
        y=y_axis,
        text="caption:N",
        size=alt.condition(alt.datum.r >= radius_cut, alt.value(16), alt.value(12)),
        color=alt.Color("label_color:N", scale=None, legend=None),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.1)),
    )
)

# Title with length-scaled font size (67-char baseline → 16px default)
title_str = "Department Budget Allocation · bubble-packed · python · altair · anyplot.ai"
title_fs = max(11, round(16 * 67 / len(title_str)))
subtitle_fs = max(8, round(title_fs * 0.85))
top_share = df.groupby(DIVISION, sort=False)[BUDGET].sum().max() / df[BUDGET].sum()
top_division = df.groupby(DIVISION, sort=False)[BUDGET].sum().idxmax()
top_department = df.loc[df[BUDGET].idxmax()]

chart = (
    alt.layer(circles_layer, captions)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            subtitle=(
                f"{top_division} division leads at {top_share:.0%} of total budget — "
                f"{top_department[DEPARTMENT]} alone at ${top_department[BUDGET]}K"
            ),
            fontSize=title_fs,
            subtitleFontSize=subtitle_fs,
            subtitleColor=INK_SOFT,
            fontWeight="bold",
            anchor="middle",
            color=INK,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Centre on the exact 2400 × 2400 square canvas (never crop)
TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
