""" pyplots.ai
area-basic: Basic Area Chart
Library: matplotlib 3.10.8 | Python 3.14.2
Quality: 90/100 | Created: 2025-12-23
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path


# Data - daily website visitors over a month with weekend dips and a viral spike
np.random.seed(42)
days = np.arange(1, 31)
base_visitors = 3000 + np.linspace(0, 2000, 30)  # Upward trend from 3k to 5k
weekend_effect = np.array([-1200 if d % 7 in (0, 6) else 0 for d in days])  # Weekend dips
noise = np.random.randn(30) * 300
visitors = base_visitors + weekend_effect + noise
# Viral blog post spike on day 18
visitors[17] = 8200
visitors[18] = 6800
visitors = np.clip(visitors, 1000, 10000)

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

y_max = visitors.max() * 1.12

# Gradient fill using imshow clipped to the area shape
cmap = mcolors.LinearSegmentedColormap.from_list("area_grad", ["#d6e6f5", "#306998"])
gradient = np.linspace(0, 1, 256).reshape(-1, 1)
gradient = np.hstack([gradient, gradient])

# Build clip path from area polygon
verts = [(days[0], 0)]
for d, v in zip(days, visitors, strict=True):
    verts.append((d, v))
verts.append((days[-1], 0))
verts.append((days[0], 0))
codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]
clip_path = Path(verts, codes)

im = ax.imshow(
    gradient, aspect="auto", cmap=cmap, alpha=0.6, extent=[days[0], days[-1], 0, y_max], origin="lower", zorder=1
)
patch = PathPatch(clip_path, transform=ax.transData, facecolor="none", edgecolor="none")
ax.add_patch(patch)
im.set_clip_path(patch)

# Solid line on top
ax.plot(days, visitors, color="#306998", linewidth=3, zorder=3)

# Annotate the viral spike
ax.annotate(
    "Viral post",
    xy=(18, visitors[17]),
    xytext=(22, visitors[17] + 400),
    fontsize=16,
    color="#306998",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 2},
    zorder=4,
)

# Labels and styling
ax.set_xlabel("Day of Month", fontsize=20)
ax.set_ylabel("Daily Visitors (count)", fontsize=20)
ax.set_title("Website Traffic · area-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Set axis limits
ax.set_xlim(1, 30)
ax.set_ylim(0, y_max)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
