"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Imprint sequential colormap (single polarity), used for the Sharpe ratio coloring
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Constants
RISK_FREE = 0.02  # annualized risk-free rate for the Sharpe ratio and the capital market line

# Columns: set these to your table's column names
RISK = "Risk (standard deviation)"  # role: risk
RETURN = "Expected return"  # role: return

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
# One row per random portfolio: its annualized risk and expected return.
rng = np.random.default_rng(42)
asset_returns = np.array([0.08, 0.10, 0.12, 0.15, 0.18])
asset_cov = np.array(
    [
        [0.04, 0.01, 0.02, 0.01, 0.02],
        [0.01, 0.06, 0.02, 0.03, 0.02],
        [0.02, 0.02, 0.09, 0.04, 0.03],
        [0.01, 0.03, 0.04, 0.12, 0.05],
        [0.02, 0.02, 0.03, 0.05, 0.16],
    ]
)
weights = rng.random((300, len(asset_returns)))
weights /= weights.sum(axis=1, keepdims=True)
df = pd.DataFrame(
    {RISK: np.sqrt(np.einsum("ij,jk,ik->i", weights, asset_cov, weights)), RETURN: weights @ asset_returns}
)

# Plot: reads only df and the constants above
SHARPE = "Sharpe ratio"
PORTFOLIO = "Portfolio"
CURVE = "Curve"
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

cloud_df = df.dropna(subset=[RISK, RETURN]).copy()
cloud_df[SHARPE] = (cloud_df[RETURN] - RISK_FREE) / cloud_df[RISK]

# Efficient frontier: the upper convex hull of the cloud, from its lowest-risk portfolio
# up to its highest-return portfolio (no portfolio of the sample lies above it)
ordered = cloud_df.sort_values([RISK, RETURN])[[RISK, RETURN]].to_numpy()
hull = []
for point in ordered:
    while len(hull) >= 2:
        a, b = hull[-1] - hull[-2], point - hull[-2]
        if a[0] * b[1] - a[1] * b[0] < 0:
            break
        hull.pop()
    hull.append(point)
frontier_df = pd.DataFrame(hull, columns=[RISK, RETURN])
frontier_df = frontier_df.iloc[: frontier_df[RETURN].argmax() + 1]

min_risk_point = frontier_df.iloc[0]
tangent_idx = ((frontier_df[RETURN] - RISK_FREE) / frontier_df[RISK]).idxmax()
tangent_risk = frontier_df.loc[tangent_idx, RISK]
tangent_return = frontier_df.loc[tangent_idx, RETURN]

cml_risk = np.array([0.0, tangent_risk * 1.5])
cml_df = pd.DataFrame({RISK: cml_risk, RETURN: RISK_FREE + (tangent_return - RISK_FREE) / tangent_risk * cml_risk})

frontier_df[CURVE] = "Efficient frontier"
cml_df[CURVE] = "Capital market line"
curves_df = pd.concat([frontier_df, cml_df], ignore_index=True)

key_df = pd.DataFrame(
    {
        PORTFOLIO: ["Minimum variance", "Maximum Sharpe ratio", "Risk-free rate"],
        RISK: [min_risk_point[RISK], tangent_risk, 0.0],
        RETURN: [min_risk_point[RETURN], tangent_return, RISK_FREE],
    }
)

x_enc = alt.X(
    RISK.translate(ESCAPE),
    type="quantitative",
    title=RISK,
    scale=alt.Scale(domain=[0, curves_df[RISK].max() * 1.05], nice=False),
)
y_enc = alt.Y(
    RETURN.translate(ESCAPE),
    type="quantitative",
    title=RETURN,
    scale=alt.Scale(domain=[0, curves_df[RETURN].max() * 1.08], nice=False),
    axis=alt.Axis(format=".0%"),
)

cloud = (
    alt.Chart(cloud_df)
    .mark_circle(size=45, opacity=0.65)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            SHARPE,
            type="quantitative",
            title=SHARPE,
            scale=alt.Scale(range=IMPRINT_SEQ),
            legend=alt.Legend(orient="right", gradientLength=110, direction="vertical"),
        ),
        tooltip=[
            alt.Tooltip(RISK.translate(ESCAPE), title=RISK, format=".3f"),
            alt.Tooltip(RETURN.translate(ESCAPE), title=RETURN, format=".3f"),
            alt.Tooltip(SHARPE, title=SHARPE, format=".2f"),
        ],
    )
)

curves = (
    alt.Chart(curves_df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            CURVE,
            type="nominal",
            title=None,
            scale=alt.Scale(domain=["Efficient frontier", "Capital market line"], range=[INK, IMPRINT_PALETTE[4]]),
            legend=alt.Legend(symbolType="stroke", symbolStrokeWidth=3),
        ),
        strokeDash=alt.StrokeDash(
            CURVE,
            type="nominal",
            scale=alt.Scale(domain=["Efficient frontier", "Capital market line"], range=[[1, 0], [6, 4]]),
            legend=None,
        ),
        order=alt.Order(CURVE, type="nominal"),
    )
)

key_points = (
    alt.Chart(key_df)
    .mark_point(size=170, filled=True, stroke=PAGE_BG, strokeWidth=1.5, opacity=1)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            PORTFOLIO,
            type="nominal",
            title="Key portfolios",
            scale=alt.Scale(
                domain=key_df[PORTFOLIO].tolist(), range=[IMPRINT_PALETTE[1], IMPRINT_PALETTE[3], IMPRINT_PALETTE[5]]
            ),
            legend=alt.Legend(symbolType="diamond"),
        ),
        shape=alt.Shape(
            PORTFOLIO,
            type="nominal",
            scale=alt.Scale(domain=key_df[PORTFOLIO].tolist(), range=["diamond", "square", "triangle-up"]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(PORTFOLIO, title=PORTFOLIO),
            alt.Tooltip(RISK.translate(ESCAPE), title=RISK, format=".3f"),
            alt.Tooltip(RETURN.translate(ESCAPE), title=RETURN, format=".3f"),
        ],
    )
)

title = "frontier-efficient · python · altair · anyplot.ai"
chart = (
    alt.layer(cloud, curves, key_points)
    .resolve_scale(color="independent", shape="independent", strokeDash="independent")
    .properties(
        width=580,
        height=390,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title(title, fontSize=16, anchor="middle"),
    )
    .configure_view(continuousWidth=580, continuousHeight=390, fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        padding=6,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=10,
        labelFontSize=9,
        symbolSize=90,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the render to the canonical 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair render {img.size} exceeds the {TW}x{TH} target; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
