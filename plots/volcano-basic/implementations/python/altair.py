""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FC_THRESHOLD = 1.0  # |log2 fold change| of 1 is a 2-fold change
P_THRESHOLD = 1.3  # -log10(0.05)
UP, DOWN, NOT_SIGNIFICANT = "Up-regulated", "Down-regulated", "Not significant"
STATUS_COLORS = {
    UP: IMPRINT_PALETTE[4],
    DOWN: IMPRINT_PALETTE[2],
    NOT_SIGNIFICANT: MUTED,
}  # semantic: red up, blue down

# Columns: set these to your table's column names
LOG2FC = "Log₂ fold change"  # role: log2_fold_change
NEGLOG10P = "-Log₁₀ (p-value)"  # role: neg_log10_pvalue

# Data: replace this block with your own table, for example df = pd.read_csv("differential_expression.csv")
rng = np.random.default_rng(42)
n_features = 2000
log2_fc = rng.normal(0, 1.4, n_features)
base_p = rng.beta(1, 8, n_features)
p_values = np.clip(base_p * np.exp(-np.abs(log2_fc) * 1.1) * rng.uniform(0.01, 1, n_features), 1e-12, 1)
df = pd.DataFrame({LOG2FC: log2_fc, NEGLOG10P: -np.log10(p_values)})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field, y_field = LOG2FC.translate(ESCAPE), NEGLOG10P.translate(ESCAPE)

passes_p = df[NEGLOG10P] >= P_THRESHOLD
df["Status"] = np.select(
    [passes_p & (df[LOG2FC] >= FC_THRESHOLD), passes_p & (df[LOG2FC] <= -FC_THRESHOLD)],
    [UP, DOWN],
    default=NOT_SIGNIFICANT,
)

x_limit = float(np.ceil(df[LOG2FC].abs().max()))
y_top = float(df[NEGLOG10P].max() * 1.05)

points = (
    alt.Chart(df)
    .mark_circle(size=34, opacity=0.55)
    .encode(
        x=alt.X(x_field, type="quantitative", title=LOG2FC, scale=alt.Scale(domain=[-x_limit, x_limit], nice=False)),
        y=alt.Y(y_field, type="quantitative", title=NEGLOG10P, scale=alt.Scale(domain=[0, y_top], nice=False)),
        color=alt.Color(
            "Status",
            type="nominal",
            title="Significance",
            scale=alt.Scale(domain=list(STATUS_COLORS), range=list(STATUS_COLORS.values())),
            legend=alt.Legend(symbolOpacity=1, symbolSize=120),
        ),
        order=alt.Order("Status", sort="descending"),
        tooltip=[
            alt.Tooltip(x_field, type="quantitative", title=LOG2FC, format=".2f"),
            alt.Tooltip(y_field, type="quantitative", title=NEGLOG10P, format=".2f"),
            alt.Tooltip("Status", type="nominal", title="Significance"),
        ],
    )
)

rule_style = {"strokeDash": [6, 4], "strokeWidth": 1.4, "color": INK, "opacity": 0.8}
vlines = alt.Chart(pd.DataFrame({"x": [-FC_THRESHOLD, FC_THRESHOLD]})).mark_rule(**rule_style).encode(x="x:Q")
hline = alt.Chart(pd.DataFrame({"y": [P_THRESHOLD]})).mark_rule(**rule_style).encode(y="y:Q")

chart = (
    (points + vlines + hline)
    .properties(
        width=590,
        height=320,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 12},
        title=alt.Title("volcano-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridColor=INK,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        titleFontSize=11,
        labelFontSize=10,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        padding=8,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
)

# Output: pad (never crop) the PNG to the 3200 x 1800 landscape target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink the view")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
