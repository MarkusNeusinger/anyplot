"""pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: altair 6.0.0 | Python 3.14.3
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
        np.linspace(0.001, 0.5, 150),
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
    prev, curr = all_roots[i - 1], all_roots[i]
    dist = np.abs(prev[:, None] - curr[None, :])
    order = np.zeros(n_roots, dtype=int)
    used = set()
    for j in range(n_roots):
        dists = [(dist[j, m], m) for m in range(n_roots) if m not in used]
        _, best = min(dists)
        used.add(best)
        order[j] = best
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
breakaway_df = pd.DataFrame({"bx": [(-6 + np.sqrt(12)) / 6], "by": [0.0], "label": ["Breakaway (s ≈ −0.42)"]})

# Damping ratio guide lines (ζ = 0.2, 0.4, 0.6, 0.8)
damping_rows = []
for zeta in [0.2, 0.4, 0.6, 0.8]:
    angle = np.pi - np.arccos(zeta)
    for side, sign in [("upper", 1), ("lower", -1)]:
        seg = f"ζ={zeta}_{side}"
        damping_rows.append({"gx": 0.0, "gy": 0.0, "seg": seg, "ord": 0})
        damping_rows.append({"gx": 5.0 * np.cos(angle), "gy": sign * 5.0 * np.sin(angle), "seg": seg, "ord": 1})
damping_df = pd.DataFrame(damping_rows)

# Damping ratio labels at end of guide lines
damping_label_rows = []
for zeta in [0.4, 0.8]:
    angle = np.pi - np.arccos(zeta)
    damping_label_rows.append({"lx": 4.6 * np.cos(angle), "ly": 4.6 * np.sin(angle), "label": f"ζ={zeta}"})
damping_label_df = pd.DataFrame(damping_label_rows)

# Natural frequency arcs (ωn = 1, 2, 3, 4) in left half-plane
wn_rows = []
for wn in [1.0, 2.0, 3.0, 4.0]:
    theta = np.linspace(np.pi / 2, 3 * np.pi / 2, 60)
    for j, t in enumerate(theta):
        wn_rows.append({"gx": wn * np.cos(t), "gy": wn * np.sin(t), "wn": f"ωn={wn}", "ord": j})
wn_df = pd.DataFrame(wn_rows)

# Real axis segments: (-1, 0) and (-∞, -2)
real_axis_df = pd.DataFrame(
    {
        "rx": [-1.0, 0.0, -5.0, -2.0],
        "ry": [0.0, 0.0, 0.0, 0.0],
        "seg": ["seg1", "seg1", "seg2", "seg2"],
        "ord": [0, 1, 0, 1],
    }
)

# Arrow direction indicators along complex branches
arrows = []
for b in range(n_roots):
    for idx in [350, 500]:
        if idx + 5 < len(gains):
            r0 = all_roots[idx, b]
            if abs(r0.imag) > 0.3:
                arrows.append({"ax": float(r0.real), "ay": float(r0.imag), "branch": f"Branch {b + 1}"})
arrow_df = pd.DataFrame(arrows) if arrows else pd.DataFrame({"ax": [], "ay": [], "branch": []})

# Equal-scaling axes centered on origin (square canvas, equal domain = equal scaling)
x_scale = alt.Scale(domain=[-5.0, 5.0], nice=False)
y_scale = alt.Scale(domain=[-5.0, 5.0], nice=False)

branch_palette = ["#306998", "#e07b39", "#2ca02c"]
branch_domain = ["Branch 1", "Branch 2", "Branch 3"]

# Layer: Locus branches — FIRST so its axis config takes effect
locus_layer = (
    alt.Chart(locus_df)
    .mark_line(strokeWidth=2.8, opacity=0.92)
    .encode(
        x=alt.X(
            "real:Q",
            scale=x_scale,
            title="Real Axis (σ)",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=21,
                titleFontWeight="bold",
                titleColor="#2a2a2a",
                labelColor="#444444",
                grid=False,
                tickCount=6,
                titlePadding=14,
                domainColor="#888888",
                tickColor="#888888",
            ),
        ),
        y=alt.Y(
            "imaginary:Q",
            scale=y_scale,
            title="Imaginary Axis (jω)",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=21,
                titleFontWeight="bold",
                titleColor="#2a2a2a",
                labelColor="#444444",
                grid=False,
                tickCount=6,
                titlePadding=14,
                domainColor="#888888",
                tickColor="#888888",
            ),
        ),
        color=alt.Color(
            "branch:N",
            scale=alt.Scale(domain=branch_domain, range=branch_palette),
            legend=alt.Legend(
                title="Branch",
                titleFontSize=16,
                labelFontSize=14,
                symbolSize=180,
                symbolStrokeWidth=3,
                orient="top-right",
                offset=5,
            ),
        ),
        order="idx:Q",
        tooltip=[
            alt.Tooltip("branch:N", title="Branch"),
            alt.Tooltip("real:Q", title="σ", format=".3f"),
            alt.Tooltip("imaginary:Q", title="jω", format=".3f"),
            alt.Tooltip("gain:Q", title="Gain K", format=".2f"),
        ],
    )
)

# Layer: Damping ratio lines
damping_layer = (
    alt.Chart(damping_df)
    .mark_line(strokeWidth=0.8, strokeDash=[6, 4], color="#d0d0d0")
    .encode(x=alt.X("gx:Q", scale=x_scale), y=alt.Y("gy:Q", scale=y_scale), detail="seg:N", order="ord:Q")
)

# Layer: Damping ratio labels
damping_label_layer = (
    alt.Chart(damping_label_df)
    .mark_text(fontSize=12, color="#aaaaaa", fontStyle="italic", align="center")
    .encode(x=alt.X("lx:Q", scale=x_scale), y=alt.Y("ly:Q", scale=y_scale), text="label:N")
)

# Layer: Natural frequency arcs
wn_layer = (
    alt.Chart(wn_df)
    .mark_line(strokeWidth=0.8, strokeDash=[4, 4], color="#d0d0d0")
    .encode(x=alt.X("gx:Q", scale=x_scale), y=alt.Y("gy:Q", scale=y_scale), detail="wn:N", order="ord:Q")
)

# Layer: Real axis segments
real_axis_layer = (
    alt.Chart(real_axis_df)
    .mark_line(strokeWidth=5, color="#306998", opacity=0.25)
    .encode(x=alt.X("rx:Q", scale=x_scale), y=alt.Y("ry:Q", scale=y_scale), detail="seg:N", order="ord:Q")
)

# Layer: Open-loop poles (× markers)
poles_layer = (
    alt.Chart(poles_df)
    .mark_point(shape="cross", size=450, strokeWidth=3.5, color="#d62728", filled=False)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title=""), alt.Tooltip("real:Q", title="σ")],
    )
)

# Layer: Imaginary axis crossings
crossing_layer = (
    alt.Chart(crossing_df)
    .mark_point(shape="diamond", size=400, strokeWidth=2.5, color="#d62728", filled=True)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title="Crossing")],
    )
)

# Layer: Crossing labels
crossing_text = (
    alt.Chart(crossing_df)
    .mark_text(fontSize=17, fontWeight="bold", color="#c5211e", align="left", dx=20, font="sans-serif")
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

# Layer: Breakaway point
breakaway_layer = (
    alt.Chart(breakaway_df)
    .mark_point(shape="square", size=220, color="#555555", filled=True, opacity=0.8)
    .encode(
        x=alt.X("bx:Q", scale=x_scale), y=alt.Y("by:Q", scale=y_scale), tooltip=[alt.Tooltip("label:N", title="Point")]
    )
)

# Layer: Arrow direction indicators
arrow_up_df = arrow_df[arrow_df["ay"] > 0] if len(arrow_df) > 0 else arrow_df
arrow_down_df = arrow_df[arrow_df["ay"] <= 0] if len(arrow_df) > 0 else arrow_df

arrow_up_layer = (
    alt.Chart(arrow_up_df)
    .mark_point(shape="triangle-up", size=250, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color("branch:N", scale=alt.Scale(domain=branch_domain, range=branch_palette), legend=None),
    )
)

arrow_down_layer = (
    alt.Chart(arrow_down_df)
    .mark_point(shape="triangle-down", size=250, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color("branch:N", scale=alt.Scale(domain=branch_domain, range=branch_palette), legend=None),
    )
)

# Compose — locus_layer first so its axis config renders
chart = (
    (
        locus_layer
        + damping_layer
        + damping_label_layer
        + wn_layer
        + real_axis_layer
        + poles_layer
        + crossing_layer
        + crossing_text
        + breakaway_layer
        + arrow_up_layer
        + arrow_down_layer
    )
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "root-locus-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color="#1a1a1a",
            subtitle="G(s) = 1 / s(s+1)(s+2)  ·  Closed-Loop Pole Trajectories vs Gain K",
            subtitleFontSize=18,
            subtitleColor="#555555",
            subtitlePadding=10,
            anchor="start",
            offset=10,
        ),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
