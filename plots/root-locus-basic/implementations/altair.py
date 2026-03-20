""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: altair 6.0.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Root locus for G(s) = 1 / (s(s+1)(s+2))
# Open-loop poles at s = 0, -1, -2; no zeros
# Characteristic equation: s³ + 3s² + 2s + K = 0
den_coeffs = [1.0, 3.0, 2.0, 0.0]

gains = np.concatenate(
    [
        np.linspace(0.001, 0.3, 100),
        np.linspace(0.3, 0.5, 100),
        np.linspace(0.5, 2, 200),
        np.linspace(2, 6, 150),
        np.linspace(6, 20, 150),
        np.linspace(20, 80, 100),
    ]
)
n_roots = 3
all_roots = np.zeros((len(gains), n_roots), dtype=complex)

for i, k in enumerate(gains):
    poly = np.array(den_coeffs, dtype=float)
    poly[-1] += k
    all_roots[i] = np.roots(poly)

# Sort roots into continuous branches via nearest-neighbor matching
all_roots[0] = np.sort(all_roots[0].real)
for i in range(1, len(gains)):
    prev = all_roots[i - 1]
    curr = all_roots[i]
    used = [False] * n_roots
    order = np.zeros(n_roots, dtype=int)
    for j in range(n_roots):
        best_m, best_d = -1, np.inf
        for m in range(n_roots):
            if not used[m]:
                d = abs(prev[j] - curr[m])
                if d < best_d:
                    best_d = d
                    best_m = m
        used[best_m] = True
        order[j] = best_m
    all_roots[i] = curr[order]

# Build branch dataframe
rows = []
for b in range(n_roots):
    for i in range(len(gains)):
        rows.append(
            {
                "real": float(all_roots[i, b].real),
                "imaginary": float(all_roots[i, b].imag),
                "gain": float(gains[i]),
                "branch": f"Branch {b + 1}",
                "idx": i,
            }
        )

locus_df = pd.DataFrame(rows)

# Open-loop poles
poles_df = pd.DataFrame(
    {"real": [0.0, -1.0, -2.0], "imaginary": [0.0, 0.0, 0.0], "label": ["Pole (s=0)", "Pole (s=−1)", "Pole (s=−2)"]}
)

# Imaginary axis crossing: ω = √2, K = 6
omega_cross = np.sqrt(2)
crossing_df = pd.DataFrame(
    {"real": [0.0, 0.0], "imaginary": [omega_cross, -omega_cross], "label": ["jω = j√2 (K=6)", "jω = −j√2 (K=6)"]}
)

# Breakaway point: d/ds[s(s+1)(s+2)] = 3s²+6s+2 = 0 → s ≈ -0.423
breakaway_df = pd.DataFrame({"bx": [(-6 + np.sqrt(12)) / 6], "by": [0.0], "label": ["Breakaway"]})

# Damping ratio lines (ζ = 0.2, 0.4, 0.6, 0.8)
damping_rows = []
for zeta in [0.2, 0.4, 0.6, 0.8]:
    angle = np.pi - np.arccos(zeta)
    r_max = 7.0
    for side, sign in [("upper", 1), ("lower", -1)]:
        seg_name = f"ζ={zeta}_{side}"
        damping_rows.append({"dx": 0.0, "dy": 0.0, "seg": seg_name, "ord": 0})
        damping_rows.append(
            {"dx": r_max * np.cos(angle), "dy": sign * r_max * np.sin(angle), "seg": seg_name, "ord": 1}
        )

damping_df = pd.DataFrame(damping_rows)

# Natural frequency arcs (ωn = 1, 2, 3, 4) in left half-plane
wn_rows = []
for wn in [1.0, 2.0, 3.0, 4.0]:
    theta = np.linspace(np.pi / 2, 3 * np.pi / 2, 60)
    for j, t in enumerate(theta):
        wn_rows.append({"wx": wn * np.cos(t), "wy": wn * np.sin(t), "wn": f"ωn={wn}", "ord": j})

wn_df = pd.DataFrame(wn_rows)

# Real axis segments: (-1, 0) and (-∞, -2)
real_axis_rows = []
for rx0, rx1, seg in [(-1.0, 0.0, "seg1"), (-7.0, -2.0, "seg2")]:
    real_axis_rows.append({"rx": rx0, "ry": 0.0, "seg": seg, "ord": 0})
    real_axis_rows.append({"rx": rx1, "ry": 0.0, "seg": seg, "ord": 1})

real_axis_df = pd.DataFrame(real_axis_rows)

# Arrow direction indicators along complex branches
arrows = []
for b in range(n_roots):
    for idx in [400, 600]:
        if idx + 5 < len(gains):
            r0 = all_roots[idx, b]
            if abs(r0.imag) > 0.5:
                arrows.append(
                    {
                        "ax": float(r0.real),
                        "ay": float(r0.imag),
                        "branch": f"Branch {b + 1}",
                        "shape": "triangle-up" if r0.imag > 0 else "triangle-down",
                    }
                )

arrow_df = pd.DataFrame(arrows) if arrows else pd.DataFrame({"ax": [], "ay": [], "branch": [], "shape": []})

# Scales
x_scale = alt.Scale(domain=[-7.0, 2.5], nice=False)
y_scale = alt.Scale(domain=[-6.0, 6.0], nice=False)

# Layer: Damping ratio lines
damping_layer = (
    alt.Chart(damping_df)
    .mark_line(strokeWidth=1, strokeDash=[6, 4], color="#d0d0d0")
    .encode(
        x=alt.X("dx:Q", scale=x_scale, axis=None),
        y=alt.Y("dy:Q", scale=y_scale, axis=None),
        detail="seg:N",
        order="ord:Q",
    )
)

# Layer: Natural frequency arcs
wn_layer = (
    alt.Chart(wn_df)
    .mark_line(strokeWidth=1, strokeDash=[4, 4], color="#d0d0d0")
    .encode(x=alt.X("wx:Q", scale=x_scale), y=alt.Y("wy:Q", scale=y_scale), detail="wn:N", order="ord:Q")
)

# Layer: Real axis segments
real_axis_layer = (
    alt.Chart(real_axis_df)
    .mark_line(strokeWidth=4, color="#306998", opacity=0.3)
    .encode(x=alt.X("rx:Q", scale=x_scale), y=alt.Y("ry:Q", scale=y_scale), detail="seg:N", order="ord:Q")
)

# Layer: Locus branches
branch_palette = ["#306998", "#e07b39", "#2ca02c"]
locus_layer = (
    alt.Chart(locus_df)
    .mark_line(strokeWidth=2.5, opacity=0.9)
    .encode(
        x=alt.X(
            "real:Q", scale=x_scale, title="Real Axis", axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=False)
        ),
        y=alt.Y(
            "imaginary:Q",
            scale=y_scale,
            title="Imaginary Axis",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=False),
        ),
        color=alt.Color(
            "branch:N",
            scale=alt.Scale(domain=["Branch 1", "Branch 2", "Branch 3"], range=branch_palette),
            legend=alt.Legend(
                title="Branch",
                titleFontSize=18,
                labelFontSize=16,
                symbolSize=200,
                symbolStrokeWidth=3,
                orient="top-right",
                offset=10,
            ),
        ),
        order="idx:Q",
        tooltip=[
            alt.Tooltip("branch:N", title="Branch"),
            alt.Tooltip("real:Q", title="Real", format=".3f"),
            alt.Tooltip("imaginary:Q", title="Imaginary", format=".3f"),
            alt.Tooltip("gain:Q", title="Gain K", format=".2f"),
        ],
    )
)

# Layer: Open-loop poles (× markers)
poles_layer = (
    alt.Chart(poles_df)
    .mark_point(shape="cross", size=400, strokeWidth=3.5, color="#d62728", filled=False)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title=""), alt.Tooltip("real:Q", title="Real")],
    )
)

# Layer: Imaginary axis crossings
crossing_layer = (
    alt.Chart(crossing_df)
    .mark_point(shape="diamond", size=350, strokeWidth=2.5, color="#d62728", filled=True)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title="Crossing")],
    )
)

# Layer: Crossing labels
crossing_text = (
    alt.Chart(crossing_df)
    .mark_text(fontSize=14, fontWeight="bold", color="#d62728", align="left", dx=16)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

# Layer: Breakaway point
breakaway_layer = (
    alt.Chart(breakaway_df)
    .mark_point(shape="square", size=200, color="#555555", filled=True, opacity=0.7)
    .encode(
        x=alt.X("bx:Q", scale=x_scale), y=alt.Y("by:Q", scale=y_scale), tooltip=[alt.Tooltip("label:N", title="Point")]
    )
)

# Layer: Arrow direction indicators
arrow_up = arrow_df[arrow_df["ay"] > 0] if len(arrow_df) > 0 else arrow_df
arrow_down = arrow_df[arrow_df["ay"] <= 0] if len(arrow_df) > 0 else arrow_df

arrow_up_layer = (
    alt.Chart(arrow_up)
    .mark_point(shape="triangle-up", size=220, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color(
            "branch:N", scale=alt.Scale(domain=["Branch 1", "Branch 2", "Branch 3"], range=branch_palette), legend=None
        ),
    )
)

arrow_down_layer = (
    alt.Chart(arrow_down)
    .mark_point(shape="triangle-down", size=220, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color(
            "branch:N", scale=alt.Scale(domain=["Branch 1", "Branch 2", "Branch 3"], range=branch_palette), legend=None
        ),
    )
)

# Compose
chart = (
    (
        damping_layer
        + wn_layer
        + real_axis_layer
        + locus_layer
        + poles_layer
        + crossing_layer
        + crossing_text
        + breakaway_layer
        + arrow_up_layer
        + arrow_down_layer
    )
    .properties(
        width=1400,
        height=1100,
        title=alt.Title(
            "root-locus-basic · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="G(s) = 1 / s(s+1)(s+2) — Closed-Loop Pole Trajectories vs Gain K",
            subtitleFontSize=17,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
