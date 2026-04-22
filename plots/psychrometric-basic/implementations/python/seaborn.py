""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 83/100 | Updated: 2026-03-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


np.random.seed(42)

# Constants
P_ATM = 101325  # Pa, standard atmosphere
T_DB = np.linspace(-10, 50, 500)

# --- Psychrometric equations ---


def p_sat(t):
    return np.where(t >= 0, np.exp(23.196 - 3816.44 / (t + 227.02)), np.exp(23.33 - 3841.0 / (t + 231.0)))


def w_from_rh(t, rh):
    return 0.62198 * (rh * p_sat(t)) / (P_ATM - rh * p_sat(t)) * 1000


# --- Seaborn theme and figure setup ---
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": 0.15,
        "grid.linewidth": 0.8,
        "font.family": "sans-serif",
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Colors - colorblind-safe palette with line style differentiation
rh_color = "#306998"  # Python blue
wb_color = "#D4A017"  # Gold/amber (replaces purple for colorblind safety)
enthalpy_color = "#C0392B"  # Red-brown
sv_color = "#27AE60"  # Green
comfort_color = "#306998"
process_color = "#E67E22"  # Orange

# --- Relative humidity curves (10%-100%) using seaborn lineplot ---
rh_records = []
for rh_val in np.arange(0.1, 1.01, 0.1):
    w = w_from_rh(T_DB, rh_val)
    mask = (w >= 0) & (w <= 30)
    for t, wv in zip(T_DB[mask], w[mask], strict=True):
        rh_records.append({"t": t, "w": wv, "rh": f"{int(rh_val * 100)}%"})

rh_df = pd.DataFrame(rh_records)
sns.lineplot(
    data=rh_df,
    x="t",
    y="w",
    hue="rh",
    ax=ax,
    palette={f"{int(r * 100)}%": rh_color for r in np.arange(0.1, 1.01, 0.1)},
    linewidth=1.2,
    alpha=0.7,
    legend=False,
    sort=True,
)
# Thicken 100% saturation curve
w_sat = w_from_rh(T_DB, 1.0)
mask_sat = (w_sat >= 0) & (w_sat <= 30)
ax.plot(T_DB[mask_sat], w_sat[mask_sat], color=rh_color, linewidth=2.5, alpha=1.0, zorder=3)

# Label RH curves
for rh_val in np.arange(0.1, 1.01, 0.1):
    label_t = 40 - int(rh_val * 15)
    w_label = float(w_from_rh(np.array([label_t]), rh_val)[0])
    if 0.5 < w_label < 29:
        ax.text(
            label_t,
            w_label + 0.4,
            f"{int(rh_val * 100)}%",
            fontsize=9,
            color=rh_color,
            alpha=0.85,
            ha="center",
            va="bottom",
            fontweight="bold",
        )

# --- Wet-bulb temperature lines ---
wb_records = []
for t_wb in np.arange(0, 35, 5):
    t_range = np.linspace(t_wb, min(t_wb + 35, 50), 200)
    w_sat_wb = w_from_rh(np.array([t_wb]), 1.0)[0]
    slope = -1.006 / 2501
    w_wb = w_sat_wb + slope * (t_range - t_wb) * 1000
    w_sat_limit = w_from_rh(t_range, 1.0)
    mask = (w_wb >= 0) & (w_wb <= w_sat_limit) & (w_wb <= 30)
    if np.any(mask):
        for t, wv in zip(t_range[mask], w_wb[mask], strict=True):
            wb_records.append({"t": t, "w": wv, "twb": f"{t_wb}°C"})

wb_df = pd.DataFrame(wb_records)
sns.lineplot(
    data=wb_df,
    x="t",
    y="w",
    hue="twb",
    ax=ax,
    palette={f"{int(tw)}°C": wb_color for tw in np.arange(0, 35, 5)},
    linewidth=0.9,
    alpha=0.55,
    legend=False,
    sort=True,
    linestyle="--",
)

# Label wet-bulb lines
for t_wb in np.arange(0, 35, 5):
    t_range = np.linspace(t_wb, min(t_wb + 35, 50), 200)
    w_sat_wb = w_from_rh(np.array([t_wb]), 1.0)[0]
    slope = -1.006 / 2501
    w_wb = w_sat_wb + slope * (t_range - t_wb) * 1000
    w_sat_limit = w_from_rh(t_range, 1.0)
    mask = (w_wb >= 0) & (w_wb <= w_sat_limit) & (w_wb <= 30)
    if np.any(mask):
        valid_t = t_range[mask]
        valid_w = w_wb[mask]
        ax.text(
            float(valid_t[-1]),
            max(float(valid_w[-1]) - 0.5, 0.2),
            f"{t_wb}°C",
            fontsize=8,
            color=wb_color,
            alpha=0.8,
            ha="left",
            va="top",
        )

# --- Specific volume lines (vectorized - no nested loops) ---
sv_values = np.arange(0.78, 0.96, 0.02)
t_range_sv = np.linspace(-10, 50, 200)
for sv_target in sv_values:
    # Solve analytically: sv = 0.287042 * (t+273.15) * (1 + 1.6078*w/1000) / (P_ATM/1000)
    # w_gkg = ((sv_target * P_ATM/1000) / (0.287042 * (t+273.15)) - 1) / 1.6078 * 1000
    w_for_sv = ((sv_target * P_ATM / 1000) / (0.287042 * (t_range_sv + 273.15)) - 1) / 1.6078 * 1000
    w_sat_limit = w_from_rh(t_range_sv, 1.0)
    mask = (w_for_sv >= 0) & (w_for_sv <= 30) & (w_for_sv <= w_sat_limit)
    if np.sum(mask) > 10:
        ax.plot(t_range_sv[mask], w_for_sv[mask], color=sv_color, linewidth=0.7, alpha=0.45, linestyle=":")
        valid_t = t_range_sv[mask]
        valid_w = w_for_sv[mask]
        mid = len(valid_t) // 3
        if mid > 0:
            ax.text(
                valid_t[mid],
                valid_w[mid],
                f"{sv_target:.2f}",
                fontsize=8,
                color=sv_color,
                alpha=0.7,
                ha="center",
                va="bottom",
                rotation=-75,
            )

# --- Enthalpy lines ---
h_values = np.arange(10, 120, 10)
t_range_h = np.linspace(-10, 50, 200)
for h_target in h_values:
    w_for_h = (h_target - 1.006 * t_range_h) / (2.501 + 0.00186 * t_range_h)
    w_sat_limit = w_from_rh(t_range_h, 1.0)
    mask = (w_for_h >= 0) & (w_for_h <= 30) & (w_for_h <= w_sat_limit)
    if np.sum(mask) > 5:
        ax.plot(t_range_h[mask], w_for_h[mask], color=enthalpy_color, linewidth=0.7, alpha=0.4, linestyle="-.")
        valid_t = t_range_h[mask]
        valid_w = w_for_h[mask]
        if len(valid_t) > 0:
            ax.text(
                valid_t[0],
                valid_w[0] + 0.3,
                f"{h_target}",
                fontsize=8,
                color=enthalpy_color,
                alpha=0.7,
                ha="right",
                va="bottom",
                rotation=-35,
            )

# --- Comfort zone (20-26°C, 30-60% RH) ---
comfort_t = np.array([20, 26, 26, 20, 20])
comfort_w = np.array(
    [
        w_from_rh(np.array([20]), 0.30)[0],
        w_from_rh(np.array([26]), 0.30)[0],
        w_from_rh(np.array([26]), 0.60)[0],
        w_from_rh(np.array([20]), 0.60)[0],
        w_from_rh(np.array([20]), 0.30)[0],
    ]
)
ax.fill(comfort_t, comfort_w, alpha=0.12, color=comfort_color, zorder=2)
ax.plot(comfort_t, comfort_w, color=comfort_color, linewidth=1.5, alpha=0.5, zorder=2)
ax.text(
    23,
    (comfort_w[0] + comfort_w[2]) / 2,
    "Comfort\nZone",
    fontsize=11,
    color=comfort_color,
    ha="center",
    va="center",
    fontweight="bold",
    alpha=0.7,
)

# --- HVAC process path using seaborn scatterplot ---
state_points = pd.DataFrame(
    {
        "t": [35, 13, 24],
        "w": [
            w_from_rh(np.array([35]), 0.50)[0],
            w_from_rh(np.array([13]), 1.0)[0],
            w_from_rh(np.array([24]), 0.50)[0],
        ],
        "label": ["A (35°C, 50%)", "B (13°C, 100%)", "C (24°C, 50%)"],
    }
)

# Process arrows
ax.annotate(
    "",
    xy=(state_points["t"][1], state_points["w"][1]),
    xytext=(state_points["t"][0], state_points["w"][0]),
    arrowprops={"arrowstyle": "->", "color": process_color, "lw": 2.5},
    zorder=5,
)
ax.annotate(
    "",
    xy=(state_points["t"][2], state_points["w"][2]),
    xytext=(state_points["t"][1], state_points["w"][1]),
    arrowprops={"arrowstyle": "->", "color": process_color, "lw": 2.5},
    zorder=5,
)

# State points via seaborn scatterplot
sns.scatterplot(
    data=state_points,
    x="t",
    y="w",
    ax=ax,
    color=process_color,
    s=120,
    zorder=6,
    legend=False,
    edgecolor="white",
    linewidth=1.5,
)

# State point labels
for _, row in state_points.iterrows():
    offset_x = -5 if "B" in row["label"] else (1.0 if "C" in row["label"] else 0.8)
    offset_y = 0.5 if "B" in row["label"] else (-1.2 if "C" in row["label"] else 0.9)
    ax.text(row["t"] + offset_x, row["w"] + offset_y, row["label"], fontsize=10, color=process_color, fontweight="bold")

# --- Legend ---
legend_elements = [
    Line2D([0], [0], color=rh_color, linewidth=2, label="Relative Humidity"),
    Line2D([0], [0], color=wb_color, linewidth=1, linestyle="--", label="Wet-Bulb Temp"),
    Line2D([0], [0], color=enthalpy_color, linewidth=1, linestyle="-.", label="Enthalpy (kJ/kg)"),
    Line2D([0], [0], color=sv_color, linewidth=1, linestyle=":", label="Specific Volume (m³/kg)"),
    Line2D([0], [0], color=process_color, linewidth=2.5, marker="o", markersize=6, label="HVAC Process Path"),
]
ax.legend(handles=legend_elements, loc="upper left", fontsize=11, framealpha=0.9, edgecolor="#cccccc")

# --- Axis styling ---
ax.set_xlim(-10, 50)
ax.set_ylim(0, 30)
ax.set_xlabel("Dry-Bulb Temperature (°C)", fontsize=20)
ax.set_ylabel("Humidity Ratio (g/kg dry air)", fontsize=20)
ax.set_title("psychrometric-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
