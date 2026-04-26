"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: altair | Python 3.13
Quality: pending | Updated: 2026-04-26
"""

import os

import altair as alt
import pandas as pd


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette — first stage is brand green (#009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data — sales funnel example from the specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

df = pd.DataFrame({"stage": stages, "value": values})
df["percentage"] = (df["value"] / df["value"].iloc[0] * 100).round(1)
df["label"] = df["value"].astype(str) + "  ·  " + df["percentage"].astype(str) + "%"

# Centered funnel: bars span [-value/2, +value/2]; mid is always 0
df["x_start"] = -df["value"] / 2
df["x_end"] = df["value"] / 2
df["x_mid"] = 0

x_scale = alt.Scale(domain=[-620, 620])

# Funnel bars (centered, narrowing)
bars = (
    alt.Chart(df)
    .mark_bar(cornerRadius=6, height=110, stroke=PAGE_BG, strokeWidth=2)
    .encode(
        x=alt.X("x_start:Q", axis=None, scale=x_scale),
        x2="x_end:Q",
        y=alt.Y("stage:N", sort=stages, axis=alt.Axis(title=None, labelPadding=18, ticks=False, domain=False)),
        color=alt.Color("stage:N", scale=alt.Scale(domain=stages, range=OKABE_ITO), legend=None),
        tooltip=[
            alt.Tooltip("stage:N", title="Stage"),
            alt.Tooltip("value:Q", title="Count", format=","),
            alt.Tooltip("percentage:Q", title="% of top", format=".1f"),
        ],
    )
)

# Value + percentage labels positioned to the right of each bar
labels = (
    alt.Chart(df)
    .mark_text(align="left", baseline="middle", dx=14, fontSize=20, fontWeight="bold", color=INK)
    .encode(x=alt.X("x_end:Q", scale=x_scale, axis=None), y=alt.Y("stage:N", sort=stages), text="label:N")
)

chart = (
    (bars + labels)
    .properties(
        width=1400,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "Sales Funnel · funnel-basic · altair · anyplot.ai", fontSize=28, color=INK, anchor="middle", offset=20
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=20,
        labelFontWeight="bold",
        labelColor=INK,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
