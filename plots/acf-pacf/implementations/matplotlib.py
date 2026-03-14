""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from statsmodels.tsa.stattools import acf, pacf


# Data — synthetic monthly airline-style passenger counts with trend + seasonality
np.random.seed(42)
n_obs = 200
t = np.arange(n_obs)
trend = 0.5 * t
seasonal = 30 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 8, n_obs)
passengers = 100 + trend + seasonal + noise

# Compute ACF and PACF
n_lags = 36
acf_values, acf_confint = acf(passengers, nlags=n_lags, alpha=0.05)
pacf_values, pacf_confint = pacf(passengers, nlags=n_lags, alpha=0.05)

acf_lags = np.arange(len(acf_values))
pacf_lags = np.arange(1, len(pacf_values))

# Confidence bounds
confidence_bound = 1.96 / np.sqrt(n_obs)

# Color palette
SIGNIFICANT_COLOR = "#306998"
INSIGNIFICANT_COLOR = "#a8c4d8"
CONF_COLOR = "#8a7060"
BG_COLOR = "#fafbfd"

# Classify significance
acf_significant = np.abs(acf_values) > confidence_bound
pacf_significant = np.abs(pacf_values[1:]) > confidence_bound

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True)
fig.set_facecolor(BG_COLOR)
ax1.set_facecolor(BG_COLOR)
ax2.set_facecolor(BG_COLOR)

# --- ACF (top subplot) ---
acf_segments = [[(lag, 0), (lag, val)] for lag, val in zip(acf_lags, acf_values, strict=False)]
acf_colors = [SIGNIFICANT_COLOR if sig else INSIGNIFICANT_COLOR for sig in acf_significant]
ax1.add_collection(LineCollection(acf_segments, colors=acf_colors, linewidths=2.8, zorder=3))

acf_sig_mask = np.array(acf_significant)
if acf_sig_mask.any():
    ax1.scatter(
        acf_lags[acf_sig_mask],
        acf_values[acf_sig_mask],
        color=SIGNIFICANT_COLOR,
        s=64,
        zorder=5,
        edgecolors="white",
        linewidths=0.8,
    )
if (~acf_sig_mask).any():
    ax1.scatter(
        acf_lags[~acf_sig_mask],
        acf_values[~acf_sig_mask],
        color=INSIGNIFICANT_COLOR,
        s=44,
        zorder=5,
        edgecolors="white",
        linewidths=0.6,
    )

ax1.axhline(y=0, color="#333333", linewidth=0.6)
ax1.axhline(y=confidence_bound, color=CONF_COLOR, linestyle="--", linewidth=1.5, alpha=0.5)
ax1.axhline(y=-confidence_bound, color=CONF_COLOR, linestyle="--", linewidth=1.5, alpha=0.5)
ax1.fill_between(acf_lags, -confidence_bound, confidence_bound, color=CONF_COLOR, alpha=0.06, zorder=1)

# Annotate seasonal spike at lag 12
ax1.annotate(
    "12-month\nseasonal cycle",
    xy=(12, acf_values[12]),
    xytext=(18, acf_values[12] + 0.18),
    fontsize=13,
    fontweight="medium",
    color="#306998",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.3, "connectionstyle": "arc3,rad=-0.2"},
    ha="center",
    va="bottom",
    zorder=6,
)

ax1.set_ylabel("ACF", fontsize=20, fontweight="medium", labelpad=12)
ax1.tick_params(axis="both", labelsize=16, length=4, width=0.8)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
for spine in ["bottom", "left"]:
    ax1.spines[spine].set_linewidth(0.6)
    ax1.spines[spine].set_color("#888888")
ax1.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#999999")
ax1.set_xlim(-0.8, n_lags + 0.8)
ax1.margins(y=0.08)

# --- PACF (bottom subplot) — starts from lag 1 ---
pacf_vals = pacf_values[1:]
pacf_segments = [[(lag, 0), (lag, val)] for lag, val in zip(pacf_lags, pacf_vals, strict=False)]
pacf_colors = [SIGNIFICANT_COLOR if sig else INSIGNIFICANT_COLOR for sig in pacf_significant]
ax2.add_collection(LineCollection(pacf_segments, colors=pacf_colors, linewidths=2.8, zorder=3))

pacf_sig_mask = np.array(pacf_significant)
if pacf_sig_mask.any():
    ax2.scatter(
        pacf_lags[pacf_sig_mask],
        pacf_vals[pacf_sig_mask],
        color=SIGNIFICANT_COLOR,
        s=64,
        zorder=5,
        edgecolors="white",
        linewidths=0.8,
    )
if (~pacf_sig_mask).any():
    ax2.scatter(
        pacf_lags[~pacf_sig_mask],
        pacf_vals[~pacf_sig_mask],
        color=INSIGNIFICANT_COLOR,
        s=44,
        zorder=5,
        edgecolors="white",
        linewidths=0.6,
    )

ax2.axhline(y=0, color="#333333", linewidth=0.6)
ax2.axhline(y=confidence_bound, color=CONF_COLOR, linestyle="--", linewidth=1.5, alpha=0.5)
ax2.axhline(y=-confidence_bound, color=CONF_COLOR, linestyle="--", linewidth=1.5, alpha=0.5)
ax2.fill_between(pacf_lags, -confidence_bound, confidence_bound, color=CONF_COLOR, alpha=0.06, zorder=1)

ax2.set_ylabel("PACF", fontsize=20, fontweight="medium", labelpad=12)
ax2.set_xlabel("Lag", fontsize=20, fontweight="medium", labelpad=10)
ax2.tick_params(axis="both", labelsize=16, length=4, width=0.8)
ax2.tick_params(axis="x", which="both", bottom=True)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
for spine in ["bottom", "left"]:
    ax2.spines[spine].set_linewidth(0.6)
    ax2.spines[spine].set_color("#888888")
ax2.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#999999")
ax2.margins(y=0.08)

# Title
fig.suptitle(
    "acf-pacf · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    y=0.97,
    color="#333333",
    fontfamily="sans-serif",
)

fig.subplots_adjust(top=0.92, bottom=0.08, hspace=0.15)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
