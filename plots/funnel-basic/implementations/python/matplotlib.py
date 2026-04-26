"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: matplotlib | Python 3.13
Quality: pending | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first stage is brand green (#009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]
# Light orange #E69F00 needs dark text; pick INK so the label also
# stays legible where it overflows the narrow bottom segment.
TEXT_ON_FILL = ["white", "white", "white", "white", INK]

# Data — sales funnel example from specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = np.array([1000, 600, 400, 200, 100])

# Geometry: widths proportional to first stage value, equal-height segments
max_value = values[0]
widths = values / max_value
n = len(stages)
y_edges = np.linspace(n, 0, n + 1)
gap = 0.06

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i in range(n):
    y_top = y_edges[i] - gap / 2
    y_bot = y_edges[i + 1] + gap / 2
    w_top = widths[i]
    # Flat bottom on the last segment — trapezoid ends at the actual
    # data width instead of tapering to a decorative point.
    w_bot = widths[i + 1] if i + 1 < n else widths[i]

    y = np.array([y_top, y_bot])
    x_left = np.array([-w_top / 2, -w_bot / 2])
    x_right = np.array([w_top / 2, w_bot / 2])
    ax.fill_betweenx(y, x_left, x_right, facecolor=OKABE_ITO[i], edgecolor=PAGE_BG, linewidth=2)

    y_mid = (y_top + y_bot) / 2
    pct = (values[i] / max_value) * 100
    ax.text(
        0,
        y_mid,
        f"{stages[i]}\n{values[i]:,}  ·  {pct:.0f}%",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=TEXT_ON_FILL[i],
    )

# Style
ax.set_xlim(-0.65, 0.65)
ax.set_ylim(-0.2, n + 0.2)
ax.set_aspect("auto")
ax.axis("off")
ax.set_title("funnel-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

# Stage index axis on the left
for i in range(n):
    y_mid = (y_edges[i] + y_edges[i + 1]) / 2
    ax.text(-0.62, y_mid, f"Stage {i + 1}", ha="left", va="center", fontsize=14, color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
