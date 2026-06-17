"""anyplot.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: altair | Python 3.13
Quality: pending | Created: 2026-06-17
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — regimes mapped for max CVD separation + semantic chaos→red.
# Stable is the first categorical series, so it takes brand green (#009E73).
STABLE = "#009E73"  # Imprint pos 1 — brand green, calm fixed point (always first)
PERIOD = "#4467A3"  # Imprint pos 3 — blue, period-doubling transition
CHAOTIC = "#AE3030"  # Imprint pos 5 — matte red, semantic anchor for disorder/chaos

# Vega embeds the full dataset; 200K points is the intended density, so lift the cap
alt.data_transformers.disable_max_rows()

# Data — Logistic map: x(n+1) = r * x(n) * (1 - x(n))
np.random.seed(42)
r_values = np.linspace(2.5, 4.0, 2000)
transient = 200
iterations = 100

r_all = []
x_all = []
for r in r_values:
    x = 0.5
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(iterations):
        x = r * x * (1.0 - x)
        r_all.append(r)
        x_all.append(x)

df = pd.DataFrame({"r": r_all, "x": x_all})

# Classify each point by dynamical regime for semantic colour-coding
df["region"] = np.where(df["r"] < 3.0, "Stable", np.where(df["r"] < 3.5699, "Period-doubling", "Chaotic"))

# Key bifurcation points — staggered y so the close 3.544/3.5699 pair never overlaps
bifurcation_points = pd.DataFrame(
    {
        "r": [3.0, 3.449, 3.544, 3.5699],
        "label": ["Period-2 (r≈3.0)", "Period-4 (r≈3.45)", "Period-8 (r≈3.54)", "Chaos (r≈3.57)"],
        "y": [0.97, 0.97, 0.97, 0.50],
    }
)

# Interactive nearest-point highlight driven by a sparse transparent overlay
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["r"], empty=False)

region_scale = alt.Scale(domain=["Stable", "Period-doubling", "Chaotic"], range=[STABLE, PERIOD, CHAOTIC])

# Density scatter — tiny markers + low alpha render the cascade as a density field
points = (
    alt.Chart(df)
    .mark_circle(size=1.5, opacity=0.18)
    .encode(
        x=alt.X(
            "r:Q", title="Growth Rate (r)", scale=alt.Scale(domain=[2.5, 4.0], nice=False), axis=alt.Axis(tickCount=7)
        ),
        y=alt.Y(
            "x:Q",
            title="Steady-State Population (x)",
            scale=alt.Scale(domain=[0, 1.0], nice=False),
            axis=alt.Axis(tickCount=6),
        ),
        color=alt.Color("region:N", scale=region_scale, legend=alt.Legend(title="Regime", orient="right")),
        tooltip=[alt.Tooltip("r:Q", title="r", format=".4f"), alt.Tooltip("x:Q", title="x", format=".4f"), "region:N"],
    )
)

# Transparent sampled overlay carries the nearest-point selection cheaply
voronoi = (
    alt.Chart(df.sample(n=5000, random_state=42))
    .mark_point(size=1, opacity=0)
    .encode(x="r:Q", y="x:Q")
    .add_params(nearest)
)

# Vertical crosshair following the pointer's nearest r
crosshair = (
    alt.Chart(df.sample(n=5000, random_state=42))
    .mark_rule(color=INK_SOFT, strokeWidth=1.2, opacity=0.6)
    .encode(x="r:Q")
    .transform_filter(nearest)
)

# Dashed rules + rotated labels marking the period-doubling thresholds
rules = (
    alt.Chart(bifurcation_points)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.2, opacity=0.45, color=INK_MUTED)
    .encode(x="r:Q")
)

labels = (
    alt.Chart(bifurcation_points)
    .mark_text(fontSize=12, fontWeight="bold", color=INK_SOFT, angle=270, align="left", dy=-7)
    .encode(x="r:Q", y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1.0])), text="label:N")
)

# Compose
chart = (
    (points + voronoi + crosshair + rules + labels)
    .properties(
        width=620,
        height=275,
        background=PAGE_BG,
        title=alt.Title(
            "bifurcation-basic · python · altair · anyplot.ai",
            fontSize=16,
            fontWeight="bold",
            color=INK,
            subtitle="Logistic map period-doubling cascade from stability to chaos",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
            subtitlePadding=6,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titlePadding=8,
        labelColor=INK_SOFT,
        titleColor=INK,
        domain=False,
        tickColor=INK_SOFT,
        grid=True,
        gridColor=INK,
        gridOpacity=0.12,
    )
    .configure_legend(
        titleFontSize=11,
        labelFontSize=10,
        titleColor=INK,
        labelColor=INK_SOFT,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        padding=8,
        cornerRadius=4,
        symbolOpacity=1,
        symbolSize=160,
        symbolType="circle",
    )
)

# Save — render then pad (never crop) up to the exact landscape target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
