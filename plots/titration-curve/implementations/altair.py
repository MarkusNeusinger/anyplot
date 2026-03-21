""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Strong acid/strong base: 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
C_acid = 0.1
V_acid = 25.0
C_base = 0.1
V_equiv = C_acid * V_acid / C_base

volume = np.unique(
    np.concatenate(
        [
            np.linspace(0.1, V_equiv - 0.5, 60),
            np.linspace(V_equiv - 0.5, V_equiv - 0.01, 30),
            np.linspace(V_equiv + 0.01, V_equiv + 0.5, 30),
            np.linspace(V_equiv + 0.5, 50.0, 50),
        ]
    )
)

ph = np.zeros_like(volume)
for i, v in enumerate(volume):
    total_vol = V_acid + v
    moles_acid = C_acid * V_acid - C_base * v
    if moles_acid > 1e-10:
        ph[i] = -np.log10(moles_acid / total_vol)
    elif moles_acid < -1e-10:
        moles_base_excess = -moles_acid
        ph[i] = 14.0 + np.log10(moles_base_excess / total_vol)
    else:
        ph[i] = 7.0

# Insert the exact equivalence point
equiv_idx = np.searchsorted(volume, V_equiv)
volume = np.insert(volume, equiv_idx, V_equiv)
ph = np.insert(ph, equiv_idx, 7.0)

# Derivative (dpH/dV) using central differences
dph_dv = np.gradient(ph, volume)
dph_dv = np.nan_to_num(dph_dv, nan=0.0, posinf=0.0, neginf=0.0)

# Normalize derivative to fit on same chart (scale to 0-14 range)
dph_max = np.max(np.abs(dph_dv))
dph_scaled = dph_dv / dph_max * 12.0

df = pd.DataFrame({"volume_ml": volume, "ph": ph, "dph_dv": dph_dv, "dph_scaled": dph_scaled})

# Equivalence point data
equiv_pt = pd.DataFrame({"volume_ml": [V_equiv], "ph": [7.0]})

equiv_line = pd.DataFrame({"volume_ml": [V_equiv, V_equiv], "ph": [0, 14]})

equiv_label = pd.DataFrame(
    {"volume_ml": [V_equiv + 0.8], "ph": [3.5], "label": [f"Equivalence Point\n{V_equiv:.0f} mL, pH 7.0"]}
)

# Colors
CLR_CURVE = "#306998"
CLR_DERIV = "#E8833A"
CLR_EQUIV = "#7B2D8E"
CLR_BG = "#FAFBFC"
CLR_TITLE = "#1a1a1a"
CLR_SUBTITLE = "#555555"
CLR_AXIS = "#333333"
CLR_TICK = "#555555"
CLR_GRID = "#d0d0d0"

# Axis styling
axis_x = {
    "labelFontSize": 16,
    "titleFontSize": 20,
    "titleFontWeight": "bold",
    "titleColor": CLR_AXIS,
    "labelColor": CLR_TICK,
    "gridOpacity": 0.2,
    "gridWidth": 0.5,
    "gridColor": CLR_GRID,
    "domainColor": "#bbbbbb",
    "domainWidth": 1.5,
    "tickColor": "#bbbbbb",
    "tickSize": 6,
    "labelPadding": 6,
}

axis_y = {**axis_x, "titlePadding": 14}

x_scale = alt.Scale(domain=[0, 50])
y_scale = alt.Scale(domain=[0, 14])

# Titration curve
titration_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3.5, color=CLR_CURVE, interpolate="monotone")
    .encode(
        x=alt.X("volume_ml:Q", scale=x_scale, title="Volume of NaOH added (mL)", axis=alt.Axis(tickCount=10, **axis_x)),
        y=alt.Y("ph:Q", scale=y_scale, title="pH", axis=alt.Axis(**axis_y)),
        tooltip=[
            alt.Tooltip("volume_ml:Q", title="Volume (mL)", format=".1f"),
            alt.Tooltip("ph:Q", title="pH", format=".2f"),
        ],
    )
)

# Derivative curve (dpH/dV) - scaled overlay
deriv_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=2, color=CLR_DERIV, strokeDash=[6, 4], interpolate="monotone", opacity=0.8)
    .encode(
        x=alt.X("volume_ml:Q", scale=x_scale),
        y=alt.Y("dph_scaled:Q", scale=y_scale),
        tooltip=[
            alt.Tooltip("volume_ml:Q", title="Volume (mL)", format=".1f"),
            alt.Tooltip("dph_dv:Q", title="dpH/dV", format=".2f"),
        ],
    )
)

# Derivative label
deriv_label_df = pd.DataFrame({"volume_ml": [35.0], "ph": [2.5], "label": ["dpH/dV (scaled)"]})

deriv_label = (
    alt.Chart(deriv_label_df)
    .mark_text(fontSize=14, fontWeight="bold", color=CLR_DERIV, align="left")
    .encode(x=alt.X("volume_ml:Q", scale=x_scale), y=alt.Y("ph:Q", scale=y_scale), text="label:N")
)

# Equivalence point vertical dashed line
equiv_vline = (
    alt.Chart(equiv_line)
    .mark_line(strokeWidth=2, strokeDash=[8, 6], color=CLR_EQUIV, opacity=0.7)
    .encode(x=alt.X("volume_ml:Q", scale=x_scale), y=alt.Y("ph:Q", scale=y_scale))
)

# Equivalence point marker
equiv_marker = (
    alt.Chart(equiv_pt)
    .mark_point(size=250, shape="diamond", filled=True, color=CLR_EQUIV, stroke="white", strokeWidth=2.5)
    .encode(x=alt.X("volume_ml:Q", scale=x_scale), y=alt.Y("ph:Q", scale=y_scale))
)

# Equivalence point annotation
equiv_annotation = (
    alt.Chart(equiv_label)
    .mark_text(fontSize=15, fontWeight="bold", color=CLR_EQUIV, align="left", dx=10, lineBreak="\n")
    .encode(x=alt.X("volume_ml:Q", scale=x_scale), y=alt.Y("ph:Q", scale=y_scale), text="label:N")
)

# pH 7 reference line
ref_line_df = pd.DataFrame({"volume_ml": [0, 50], "ph": [7, 7]})
ref_line = (
    alt.Chart(ref_line_df)
    .mark_line(strokeWidth=1, strokeDash=[4, 4], color="#aaaaaa", opacity=0.5)
    .encode(x=alt.X("volume_ml:Q", scale=x_scale), y=alt.Y("ph:Q", scale=y_scale))
)

# Combine chart
chart = (
    (ref_line + titration_line + deriv_line + equiv_vline + equiv_marker + equiv_annotation + deriv_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "titration-curve · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color=CLR_TITLE,
            subtitle="HCl (0.1 M, 25 mL) titrated with NaOH (0.1 M)  ·  Strong Acid / Strong Base",
            subtitleFontSize=18,
            subtitleColor=CLR_SUBTITLE,
            subtitlePadding=10,
            anchor="start",
            offset=12,
        ),
    )
    .configure_view(strokeWidth=0, fill=CLR_BG, cornerRadius=4)
    .configure(background="#FFFFFF", padding={"left": 20, "right": 30, "top": 10, "bottom": 10})
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
