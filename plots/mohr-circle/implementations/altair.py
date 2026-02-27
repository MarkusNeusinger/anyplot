"""pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: altair | Python 3.13
Quality: pending | Created: 2026-02-27
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - stress state (MPa)
sigma_x = 80
sigma_y = -40
tau_xy = 30

center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
theta_p2 = np.degrees(np.arctan2(tau_xy, (sigma_x - sigma_y) / 2))

# Circle outline (parametric)
angles = np.linspace(0, 2 * np.pi, 361)
circle_df = pd.DataFrame(
    {"sigma": center + radius * np.cos(angles), "tau": radius * np.sin(angles), "order": range(361)}
)

# Key stress points
stress_points = pd.DataFrame(
    [
        {"sigma": sigma_x, "tau": tau_xy, "label": f"A ({sigma_x}, {tau_xy})", "type": "Stress State"},
        {"sigma": sigma_y, "tau": -tau_xy, "label": f"B ({sigma_y}, {-tau_xy})", "type": "Stress State"},
        {"sigma": sigma_1, "tau": 0, "label": f"σ₁ = {sigma_1:.1f} MPa", "type": "Principal"},
        {"sigma": sigma_2, "tau": 0, "label": f"σ₂ = {sigma_2:.1f} MPa", "type": "Principal"},
        {"sigma": center, "tau": tau_max, "label": f"τmax = {tau_max:.1f} MPa", "type": "Max Shear"},
        {"sigma": center, "tau": -tau_max, "label": "−τmax", "type": "Max Shear"},
    ]
)

# Diameter line A → B
diameter_df = pd.DataFrame({"sigma": [sigma_x, sigma_y], "tau": [tau_xy, -tau_xy]})

# 2θp angle arc
arc_r = radius * 0.25
arc_angles = np.linspace(0, np.radians(theta_p2), 50)
arc_df = pd.DataFrame(
    {"sigma": center + arc_r * np.cos(arc_angles), "tau": arc_r * np.sin(arc_angles), "order": range(50)}
)

# Equal aspect ratio domains
span = max(sigma_1 - sigma_2, 2 * tau_max) + 50
domain_sigma = [center - span / 2, center + span / 2]
domain_tau = [-span / 2, span / 2]

x_scale = alt.Scale(domain=domain_sigma)
y_scale = alt.Scale(domain=domain_tau)

# Reference lines
h_rule = (
    alt.Chart(pd.DataFrame({"tau": [0]}))
    .mark_rule(color="#999999", strokeWidth=1, opacity=0.5)
    .encode(y=alt.Y("tau:Q", scale=y_scale))
)

v_rule = (
    alt.Chart(pd.DataFrame({"sigma": [center]}))
    .mark_rule(color="#999999", strokeWidth=1, opacity=0.4, strokeDash=[6, 4])
    .encode(x=alt.X("sigma:Q", scale=x_scale))
)

# Circle
circle = (
    alt.Chart(circle_df)
    .mark_line(color="#306998", strokeWidth=2.5)
    .encode(
        x=alt.X("sigma:Q", title="Normal Stress σ (MPa)", scale=x_scale),
        y=alt.Y("tau:Q", title="Shear Stress τ (MPa)", scale=y_scale),
        order="order:Q",
    )
)

# Diameter line
diameter = (
    alt.Chart(diameter_df)
    .mark_line(color="#306998", strokeWidth=1.5, strokeDash=[8, 5], opacity=0.5)
    .encode(x="sigma:Q", y="tau:Q")
)

# 2θp arc
arc = alt.Chart(arc_df).mark_line(color="#E67E22", strokeWidth=2.5).encode(x="sigma:Q", y="tau:Q", order="order:Q")

# Angle label
angle_lbl_df = pd.DataFrame(
    {
        "sigma": [center + arc_r * 2.0 * np.cos(np.radians(theta_p2 / 2))],
        "tau": [arc_r * 2.0 * np.sin(np.radians(theta_p2 / 2))],
    }
)
angle_lbl = (
    alt.Chart(angle_lbl_df)
    .mark_text(text=f"2θp = {theta_p2:.1f}°", fontSize=16, fontWeight="bold", color="#E67E22")
    .encode(x="sigma:Q", y="tau:Q")
)

# Stress points with color by type
points = (
    alt.Chart(stress_points)
    .mark_point(size=300, filled=True, strokeWidth=2, stroke="white")
    .encode(
        x="sigma:Q",
        y="tau:Q",
        color=alt.Color(
            "type:N",
            scale=alt.Scale(domain=["Stress State", "Principal", "Max Shear"], range=["#306998", "#C0392B", "#E67E22"]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("label:N", title="Point"),
            alt.Tooltip("sigma:Q", title="σ (MPa)", format=".1f"),
            alt.Tooltip("tau:Q", title="τ (MPa)", format=".1f"),
        ],
    )
)

# Center point
center_pt_df = pd.DataFrame({"sigma": [center], "tau": [0]})
center_pt = (
    alt.Chart(center_pt_df)
    .mark_point(size=200, filled=True, color="#999999", strokeWidth=2, stroke="white")
    .encode(x="sigma:Q", y="tau:Q")
)
center_lbl = (
    alt.Chart(center_pt_df)
    .mark_text(text=f"C ({center:.0f}, 0)", fontSize=14, color="#666666", dy=22)
    .encode(x="sigma:Q", y="tau:Q")
)

# Labels grouped by offset direction
# Upper-right: A, σ₁, τmax
ur_df = stress_points.iloc[[0, 2, 4]]
ur_labels = (
    alt.Chart(ur_df)
    .mark_text(fontSize=15, fontWeight="bold", align="left", dx=14, dy=-14)
    .encode(x="sigma:Q", y="tau:Q", text="label:N")
)

# Upper-left: σ₂
ul_df = stress_points.iloc[[3]]
ul_labels = (
    alt.Chart(ul_df)
    .mark_text(fontSize=15, fontWeight="bold", align="right", dx=-14, dy=-14)
    .encode(x="sigma:Q", y="tau:Q", text="label:N")
)

# Lower-left: B
ll_df = stress_points.iloc[[1]]
ll_labels = (
    alt.Chart(ll_df)
    .mark_text(fontSize=15, fontWeight="bold", align="right", dx=-14, dy=18)
    .encode(x="sigma:Q", y="tau:Q", text="label:N")
)

# Lower-right: −τmax
lr_df = stress_points.iloc[[5]]
lr_labels = (
    alt.Chart(lr_df)
    .mark_text(fontSize=15, fontWeight="bold", align="left", dx=14, dy=18)
    .encode(x="sigma:Q", y="tau:Q", text="label:N")
)

# Combine all layers
chart = (
    alt.layer(
        h_rule,
        v_rule,
        circle,
        diameter,
        arc,
        points,
        center_pt,
        ur_labels,
        ul_labels,
        ll_labels,
        lr_labels,
        center_lbl,
        angle_lbl,
    )
    .properties(width=1200, height=1200, title=alt.Title("mohr-circle · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
