""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: altair 6.0.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Nyquist plot for G(s) = 5 / ((s+1)(0.5s+1)(0.1s+1))
# A stable third-order system with DC gain = 5
omega = np.concatenate(
    [np.logspace(-2, -0.5, 100), np.logspace(-0.5, 0.5, 250), np.logspace(0.5, 1.5, 200), np.logspace(1.5, 3, 100)]
)

K = 5.0
s = 1j * omega
G = K / ((s + 1.0) * (0.5 * s + 1.0) * (0.1 * s + 1.0))

real_part = G.real
imag_part = G.imag

# Positive frequency branch
pos_df = pd.DataFrame(
    {
        "real": real_part,
        "imaginary": imag_part,
        "frequency": omega,
        "branch": "ω ≥ 0 (positive)",
        "idx": np.arange(len(omega)),
    }
)

# Negative frequency branch (mirror about real axis)
neg_df = pd.DataFrame(
    {
        "real": real_part,
        "imaginary": -imag_part,
        "frequency": -omega[::-1],
        "branch": "ω ≤ 0 (negative)",
        "idx": np.arange(len(omega)),
    }
)

nyquist_df = pd.concat([pos_df, neg_df], ignore_index=True)

# Unit circle for reference
theta = np.linspace(0, 2 * np.pi, 200)
unit_circle_df = pd.DataFrame({"ux": np.cos(theta), "uy": np.sin(theta), "idx": np.arange(len(theta))})

# Critical point (-1, 0)
critical_df = pd.DataFrame({"real": [-1.0], "imaginary": [0.0], "label": ["Critical Point (−1, 0)"]})

# Find gain crossover (|G(jω)| = 1)
magnitude = np.abs(G)
gain_cross_idx = np.argmin(np.abs(magnitude - 1.0))
gain_cross_omega = omega[gain_cross_idx]

# Phase crossover: where imaginary part crosses zero (excluding near DC)
sign_changes = np.where(np.diff(np.sign(imag_part[30:])))[0] + 30
phase_cross_idx = sign_changes[0] if len(sign_changes) > 0 else None
phase_cross_omega = omega[phase_cross_idx] if phase_cross_idx is not None else None

# Frequency markers along curve — offset label_y to avoid overlaps
freq_annotations = []
for w_mark, dy_px in [(0.5, -18), (1.0, -18), (5.0, -18)]:
    idx = np.argmin(np.abs(omega - w_mark))
    freq_annotations.append(
        {"real": real_part[idx], "imaginary": imag_part[idx], "label": f"ω = {w_mark}", "dy_px": dy_px}
    )

# ω = 2.0 and gain crossover (ω ≈ 2.7) are close — place on opposite sides
idx_2 = np.argmin(np.abs(omega - 2.0))
freq_annotations.append({"real": real_part[idx_2], "imaginary": imag_part[idx_2], "label": "ω = 2.0", "dy_px": -20})
freq_annotations.append(
    {
        "real": real_part[gain_cross_idx],
        "imaginary": imag_part[gain_cross_idx],
        "label": f"ω ≈ {gain_cross_omega:.1f} (|G|=1)",
        "dy_px": 20,
    }
)

# Phase crossover is near the critical point — annotate it separately
# to avoid overlap with the critical point label
if phase_cross_idx is not None:
    phase_cross_real = real_part[phase_cross_idx]
    phase_cross_imag = imag_part[phase_cross_idx]
    phase_cross_label = f"ω ≈ {phase_cross_omega:.1f} (phase crossover)"

freq_df = pd.DataFrame(freq_annotations)

# Arrow indicators for direction of increasing frequency
arrow_rows = []
for target_w in [0.8, 3.0]:
    idx = np.argmin(np.abs(omega - target_w))
    im_val = imag_part[idx]
    if abs(im_val) > 0.05:
        shape = "down" if im_val < 0 else "up"
        arrow_rows.append({"ax": real_part[idx], "ay": imag_part[idx], "branch": "ω ≥ 0 (positive)", "shape": shape})
        arrow_rows.append(
            {
                "ax": real_part[idx],
                "ay": -imag_part[idx],
                "branch": "ω ≤ 0 (negative)",
                "shape": "up" if shape == "down" else "down",
            }
        )
arrow_df = pd.DataFrame(arrow_rows)

# Axis scales - 1:1 aspect ratio, tighter domain around data
plot_range = 5.5
x_scale = alt.Scale(domain=[-plot_range, plot_range], nice=False)
y_scale = alt.Scale(domain=[-plot_range, plot_range], nice=False)

branch_palette = ["#306998", "#e07b39"]
branch_domain = ["ω ≥ 0 (positive)", "ω ≤ 0 (negative)"]

# Layer: Nyquist curve with conditional selection highlight
highlight = alt.selection_point(fields=["branch"], bind="legend")

nyquist_layer = (
    alt.Chart(nyquist_df)
    .mark_line(strokeWidth=2.8)
    .encode(
        x=alt.X(
            "real:Q",
            scale=x_scale,
            title="Real Part — Re[G(jω)]",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=20,
                titleFontWeight="bold",
                titleColor="#2a2a2a",
                labelColor="#444444",
                grid=False,
                titlePadding=14,
                domainColor="#aaaaaa",
                tickColor="#aaaaaa",
            ),
        ),
        y=alt.Y(
            "imaginary:Q",
            scale=y_scale,
            title="Imaginary Part — Im[G(jω)]",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=20,
                titleFontWeight="bold",
                titleColor="#2a2a2a",
                labelColor="#444444",
                grid=False,
                titlePadding=14,
                domainColor="#aaaaaa",
                tickColor="#aaaaaa",
            ),
        ),
        color=alt.Color(
            "branch:N",
            scale=alt.Scale(domain=branch_domain, range=branch_palette),
            legend=alt.Legend(
                title="Frequency Branch",
                titleFontSize=16,
                labelFontSize=14,
                symbolSize=180,
                symbolStrokeWidth=3,
                orient="top-right",
                offset=5,
            ),
        ),
        opacity=alt.condition(highlight, alt.value(0.9), alt.value(0.2)),
        order="idx:Q",
        tooltip=[
            alt.Tooltip("branch:N", title="Branch"),
            alt.Tooltip("real:Q", title="Re(G)", format=".3f"),
            alt.Tooltip("imaginary:Q", title="Im(G)", format=".3f"),
            alt.Tooltip("frequency:Q", title="ω (rad/s)", format=".3f"),
        ],
    )
    .add_params(highlight)
)

# Layer: Unit circle
unit_circle_layer = (
    alt.Chart(unit_circle_df)
    .mark_line(strokeWidth=1.5, strokeDash=[6, 4], color="#cccccc", opacity=0.6)
    .encode(x=alt.X("ux:Q", scale=x_scale), y=alt.Y("uy:Q", scale=y_scale), order="idx:Q")
)

# Layer: Critical point (-1, 0) with pulsing ring
critical_ring = (
    alt.Chart(critical_df)
    .mark_point(shape="circle", size=800, strokeWidth=2, color="#d62728", filled=False, opacity=0.3)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale))
)

critical_layer = (
    alt.Chart(critical_df)
    .mark_point(shape="cross", size=500, strokeWidth=4, color="#d62728", filled=False)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title="Critical Point")],
    )
)

critical_text = (
    alt.Chart(critical_df)
    .mark_text(fontSize=16, fontWeight="bold", color="#c5211e", align="right", dx=-18, dy=-16)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

# Layer: Phase crossover annotation (positioned below critical point to avoid overlap)
phase_cross_layers = []
if phase_cross_idx is not None:
    pc_df = pd.DataFrame({"real": [phase_cross_real], "imaginary": [phase_cross_imag], "label": [phase_cross_label]})
    phase_cross_point = (
        alt.Chart(pc_df)
        .mark_point(shape="diamond", size=250, color="#8b4513", filled=True, opacity=0.85)
        .encode(
            x=alt.X("real:Q", scale=x_scale),
            y=alt.Y("imaginary:Q", scale=y_scale),
            tooltip=[alt.Tooltip("label:N", title="Phase Crossover")],
        )
    )
    phase_cross_text = (
        alt.Chart(pc_df)
        .mark_text(fontSize=13, color="#8b4513", fontWeight="bold", align="left", dx=14, dy=18)
        .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
    )
    phase_cross_layers = [phase_cross_point, phase_cross_text]

# Layer: Frequency annotation points
freq_points = (
    alt.Chart(freq_df)
    .mark_point(shape="circle", size=200, color="#306998", filled=True, opacity=0.85)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title="Frequency")],
    )
)

# Split labels by dy offset to avoid overlap (Altair mark-level dy is static)
freq_above = freq_df[freq_df["dy_px"] < 0].copy()
freq_below = freq_df[freq_df["dy_px"] > 0].copy()

freq_labels_above = (
    alt.Chart(freq_above)
    .mark_text(fontSize=14, color="#333333", fontWeight="bold", align="left", dx=14, dy=-18)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

freq_labels_below = (
    alt.Chart(freq_below)
    .mark_text(fontSize=14, color="#333333", fontWeight="bold", align="left", dx=14, dy=20)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

# Layer: Direction arrows
arrow_up_df = arrow_df[arrow_df["shape"] == "up"].copy()
arrow_down_df = arrow_df[arrow_df["shape"] == "down"].copy()

arrow_up_layer = (
    alt.Chart(arrow_up_df)
    .mark_point(shape="triangle-up", size=280, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color("branch:N", scale=alt.Scale(domain=branch_domain, range=branch_palette), legend=None),
    )
)

arrow_down_layer = (
    alt.Chart(arrow_down_df)
    .mark_point(shape="triangle-down", size=280, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color("branch:N", scale=alt.Scale(domain=branch_domain, range=branch_palette), legend=None),
    )
)

# Compose all layers
combined = (
    unit_circle_layer
    + nyquist_layer
    + critical_ring
    + critical_layer
    + critical_text
    + freq_points
    + freq_labels_above
    + freq_labels_below
    + arrow_up_layer
    + arrow_down_layer
)
for layer in phase_cross_layers:
    combined = combined + layer

chart = (
    combined.properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "nyquist-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color="#1a1a1a",
            subtitle="G(s) = 5 / (s+1)(0.5s+1)(0.1s+1)  ·  Open-Loop Frequency Response",
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
