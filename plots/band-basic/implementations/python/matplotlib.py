""" pyplots.ai
band-basic: Basic Band Plot
Library: matplotlib 3.10.8 | Python 3.14
Quality: 93/100 | Updated: 2026-02-23
"""

import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Data - Daily temperature forecast with 95% confidence interval
np.random.seed(42)
days = np.arange(1, 31)

# Central forecast: seasonal warming pattern peaking mid-month
temp_forecast = 12 + 6 * np.sin(np.pi * days / 30) + 0.1 * days

# Confidence interval widens further into the forecast (common in weather models)
uncertainty = 0.8 + 0.12 * days
temp_lower = temp_forecast - uncertainty
temp_upper = temp_forecast + uncertainty

# Colors
band_rgb = mcolors.to_rgb("#306998")
line_color = "#c4622d"

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Gradient band using pcolormesh with gouraud shading
x_fine = np.linspace(days[0], days[-1], 300)
c_fine = np.interp(x_fine, days, temp_forecast)
lo_fine = np.interp(x_fine, days, temp_lower)
hi_fine = np.interp(x_fine, days, temp_upper)

n_vert = 100
X = np.tile(x_fine, (n_vert, 1))
Y = np.zeros((n_vert, len(x_fine)))
C = np.zeros((n_vert, len(x_fine)))

for j in range(len(x_fine)):
    Y[:, j] = np.linspace(lo_fine[j], hi_fine[j], n_vert)
    hw = (hi_fine[j] - lo_fine[j]) / 2
    C[:, j] = 1 - np.abs(Y[:, j] - c_fine[j]) / hw

cmap = mcolors.LinearSegmentedColormap.from_list("ci", [(*band_rgb, 0.02), (*band_rgb, 0.20), (*band_rgb, 0.42)])
ax.pcolormesh(X, Y, C, cmap=cmap, shading="gouraud", rasterized=True, zorder=1)

# Boundary lines (increased visibility)
ax.plot(days, temp_lower, color="#306998", lw=1.8, ls="--", alpha=0.65, zorder=2)
ax.plot(days, temp_upper, color="#306998", lw=1.8, ls="--", alpha=0.65, zorder=2)

# Center line with glow effect (distinctive path_effects)
ax.plot(
    days,
    temp_forecast,
    color=line_color,
    linewidth=3,
    zorder=3,
    path_effects=[pe.Stroke(linewidth=6, foreground=line_color, alpha=0.2), pe.Normal()],
)

# Annotation: highlight where forecast uncertainty grows large
threshold_idx = int(np.argmax(uncertainty > 3.0))
ax.annotate(
    "Uncertainty exceeds \u00b13\u00b0C",
    xy=(days[threshold_idx], temp_lower[threshold_idx]),
    xytext=(days[threshold_idx] + 5, temp_lower[threshold_idx] - 2),
    fontsize=14,
    color="#444444",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.5, "connectionstyle": "arc3,rad=0.2"},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    zorder=4,
)

# Custom legend
legend_handles = [
    Patch(facecolor="#306998", alpha=0.3, edgecolor="#306998", label="95% Confidence Interval"),
    plt.Line2D([0], [0], color=line_color, linewidth=3, label="Forecast Mean"),
]
ax.legend(handles=legend_handles, fontsize=16, loc="upper left")

# Style
ax.set_xlabel("Day of Month", fontsize=20)
ax.set_ylabel("Temperature (\u00b0C)", fontsize=20)
ax.set_title("band-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
