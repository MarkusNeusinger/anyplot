""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch


# Constants
P_ATM = 101325.0  # Pa, standard atmospheric pressure

# Data
t_db = np.linspace(-10, 50, 500)

# Precomputed saturation vapor pressure (Buck equation) for t_db range
ps_db = 611.21 * np.exp((18.678 - t_db / 234.5) * (t_db / (257.14 + t_db)))
W_MAX = 30  # g/kg

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

rh_color = "#306998"
wb_color = "#1B7F8E"
enth_color = "#C75B2A"
vol_color = "#8B6BAE"

# Relative humidity curves (10% to 100%)
for rh in np.arange(0.1, 1.01, 0.1):
    w = 0.621945 * rh * ps_db / (P_ATM - rh * ps_db) * 1000
    mask = (w >= 0) & (w <= W_MAX)
    t_p, w_p = t_db[mask], w[mask]
    if len(t_p) > 0:
        lw = 2.5 if abs(rh - 1.0) < 0.01 else 1.2
        alpha = 1.0 if abs(rh - 1.0) < 0.01 else 0.6
        ax.plot(t_p, w_p, color=rh_color, linewidth=lw, alpha=alpha)
        rh_pct = int(rh * 100)
        if rh_pct == 100:
            continue
        frac = 0.75 if rh_pct <= 30 else 0.65 if rh_pct <= 60 else 0.42 + 0.025 * (100 - rh_pct)
        idx = min(int(len(t_p) * frac), len(t_p) - 1)
        if w_p[idx] < W_MAX - 3:
            ax.text(
                t_p[idx],
                w_p[idx] + 0.4,
                f"{rh_pct}%",
                fontsize=10,
                color=rh_color,
                alpha=0.85,
                ha="center",
                fontweight="medium",
            )

# Wet-bulb temperature lines
for t_wb in np.arange(0, 35, 5):
    t_range = np.linspace(t_wb, min(t_wb + 30, 50), 200)
    ps_wb = 611.21 * np.exp((18.678 - t_wb / 234.5) * (t_wb / (257.14 + t_wb)))
    ws_wb = 0.621945 * ps_wb / (P_ATM - ps_wb)
    w = np.maximum(ws_wb - 1.006e3 * (t_range - t_wb) / (2501e3 + 1.86e3 * t_range - 4.186e3 * t_wb), 0) * 1000
    mask = (w >= 0) & (w <= W_MAX) & (t_range >= -10) & (t_range <= 50)
    t_p, w_p = t_range[mask], w[mask]
    if len(t_p) > 2:
        ax.plot(t_p, w_p, color=wb_color, linewidth=1.0, alpha=0.55, linestyle="--")
        ax.text(
            t_p[0] - 0.3,
            w_p[0] + 0.3,
            f"{int(t_wb)}°C",
            fontsize=10,
            color=wb_color,
            alpha=0.8,
            rotation=-45,
            ha="right",
        )

# Enthalpy lines (kJ/kg dry air)
for h in np.arange(10, 120, 10):
    w = (h - 1.006 * t_db) / (2501 + 1.86 * t_db) * 1000
    mask = (w >= 0) & (w <= W_MAX) & (t_db >= -10) & (t_db <= 50)
    t_p, w_p = t_db[mask], w[mask]
    if len(t_p) > 2:
        ax.plot(t_p, w_p, color=enth_color, linewidth=1.0, alpha=0.55, linestyle="-.")
        if w_p[0] <= W_MAX:
            ax.text(t_p[0] - 0.5, w_p[0] + 0.2, f"{int(h)}", fontsize=9, color=enth_color, alpha=0.75, rotation=-30)

# Specific volume lines (m³/kg dry air)
for v in np.arange(0.78, 0.96, 0.02):
    t_k = t_db + 273.15
    w = (v * P_ATM / (287.055 * t_k) - 1) / 1.6078 * 1000
    mask = (w >= 0) & (w <= W_MAX) & (t_db >= -10) & (t_db <= 50)
    t_p, w_p = t_db[mask], w[mask]
    if len(t_p) > 2:
        ax.plot(t_p, w_p, color=vol_color, linewidth=1.0, alpha=0.55, linestyle=":")
        if 0 <= w_p[-1] <= W_MAX:
            ax.text(t_p[-1] + 0.3, w_p[-1], f"{v:.2f}", fontsize=9, color=vol_color, alpha=0.75, rotation=-75)

# Comfort zone (20-26°C, 30-60% RH) - inline humidity ratio calculation
comfort_temps = np.array([20, 26])
comfort_ps = 611.21 * np.exp((18.678 - comfort_temps / 234.5) * (comfort_temps / (257.14 + comfort_temps)))
comfort_w_30 = 0.621945 * 0.30 * comfort_ps / (P_ATM - 0.30 * comfort_ps) * 1000
comfort_w_60 = 0.621945 * 0.60 * comfort_ps / (P_ATM - 0.60 * comfort_ps) * 1000
comfort_polygon = np.array([[20, comfort_w_30[0]], [26, comfort_w_30[1]], [26, comfort_w_60[1]], [20, comfort_w_60[0]]])
ax.add_patch(
    mpatches.Polygon(
        comfort_polygon, closed=True, facecolor=rh_color, alpha=0.10, edgecolor=rh_color, linewidth=1.5, zorder=3
    )
)
ax.text(
    23,
    np.mean(comfort_polygon[:, 1]) - 0.8,
    "Comfort\nZone",
    fontsize=11,
    color=rh_color,
    ha="center",
    va="center",
    fontweight="bold",
    alpha=0.7,
    zorder=4,
)

# HVAC process: hot humid air → cool & dehumidify → reheat to comfort
hvac_temps = np.array([35, 13, 24])
hvac_rhs = np.array([0.50, 0.95, 0.50])
hvac_ps = 611.21 * np.exp((18.678 - hvac_temps / 234.5) * (hvac_temps / (257.14 + hvac_temps)))
hvac_w = 0.621945 * hvac_rhs * hvac_ps / (P_ATM - hvac_rhs * hvac_ps) * 1000
state_1_w, state_2_w, state_3_w = hvac_w[0], hvac_w[1], hvac_w[2]

arrow_kw = {"arrowstyle": "->", "color": "#D32F2F", "linewidth": 2.5, "mutation_scale": 20, "zorder": 5}
ax.add_patch(FancyArrowPatch((35, state_1_w), (13, state_2_w), **arrow_kw))
ax.add_patch(FancyArrowPatch((13, state_2_w), (24, state_3_w), **arrow_kw))

for t, w, label in [(35, state_1_w, "1"), (13, state_2_w, "2"), (24, state_3_w, "3")]:
    ax.plot(t, w, "o", color="#D32F2F", markersize=10, zorder=6, markeredgecolor="white", markeredgewidth=1.5)
    ax.text(t + 0.8, w + 0.5, label, fontsize=12, color="#D32F2F", fontweight="bold", zorder=6)

ax.text(
    36,
    state_1_w - 2.5,
    "Cool + Dehumidify \u2192 Reheat",
    fontsize=10,
    color="#D32F2F",
    alpha=0.85,
    fontstyle="italic",
    ha="center",
)

# Style
ax.set_xlim(-10, 50)
ax.set_ylim(0, 30)
ax.set_xlabel("Dry-Bulb Temperature (\u00b0C)", fontsize=20)
ax.set_ylabel("Humidity Ratio (g/kg dry air)", fontsize=20)
ax.set_title("psychrometric-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.6)

legend_elements = [
    Line2D([0], [0], color=rh_color, linewidth=2, label="Relative Humidity"),
    Line2D([0], [0], color=wb_color, linewidth=1, linestyle="--", label="Wet-Bulb Temp"),
    Line2D([0], [0], color=enth_color, linewidth=1, linestyle="-.", label="Enthalpy (kJ/kg)"),
    Line2D([0], [0], color=vol_color, linewidth=1, linestyle=":", label="Specific Volume (m\u00b3/kg)"),
    Line2D([0], [0], color="#D32F2F", linewidth=2, marker="o", markersize=6, label="HVAC Process"),
]
ax.legend(handles=legend_elements, fontsize=16, loc="upper left", framealpha=0.9, edgecolor="none")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
