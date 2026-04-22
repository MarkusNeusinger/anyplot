""" pyplots.ai
density-basic: Basic Density Plot
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.collections import EventCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy import stats


# Data - Response times (ms) showing bimodal server behavior
np.random.seed(42)
cached_responses = np.random.normal(45, 12, 350)  # Fast cache-hit requests
db_responses = np.random.normal(140, 25, 150)  # Slower database-query requests
response_times = np.concatenate([cached_responses, db_responses])
response_times = response_times[response_times > 0]

# Compute KDE with Silverman bandwidth selection
kde = stats.gaussian_kde(response_times, bw_method="silverman")
x_range = np.linspace(0, response_times.max() + 30, 600)
density = kde(x_range)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Vertical gradient fill (dark at base, light at top) clipped to density curve
cmap = LinearSegmentedColormap.from_list("blue_fade", ["#306998", "#c4daf0"])
gradient = np.linspace(0, 1, 256).reshape(-1, 1)
ax.imshow(
    gradient,
    extent=[x_range[0], x_range[-1], 0, density.max()],
    aspect="auto",
    cmap=cmap,
    alpha=0.5,
    origin="lower",
    zorder=1,
)
verts = np.column_stack([np.concatenate([x_range, [x_range[-1], x_range[0]]]), np.concatenate([density, [0, 0]])])
codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 1)
clip_path = PathPatch(Path(verts, codes), transform=ax.transData, facecolor="none", edgecolor="none")
ax.add_patch(clip_path)
for artist in ax.get_images():
    artist.set_clip_path(clip_path)

# Density curve
ax.plot(x_range, density, linewidth=3, color="#306998", zorder=3)

# Rug plot using EventCollection
rug = EventCollection(
    response_times, lineoffset=-0.0006, linelength=0.001, linewidth=0.8, color="#306998", alpha=0.4, zorder=2
)
ax.add_collection(rug)

# Style
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("density-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16, length=0)
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%g"))

# Grid and spines
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#888888")
ax.spines["bottom"].set_color("#888888")

# Axis limits
ax.set_xlim(x_range[0], x_range[-1])
ax.set_ylim(bottom=-0.0018)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
