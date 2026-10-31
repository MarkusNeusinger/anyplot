"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first stage is brand green (#009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

STAGE = "Stage"  # role: stage
VALUE = "Visitors"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VALUE: [1000, 600, 400, 200, 100]}
)

# Plot
# Geometry: widths proportional to first stage value, equal-height segments
n = len(df)
values = df[VALUE].to_numpy()
widths = values / values[0]
y_edges = np.linspace(n, 0, n + 1)
gap = 0.06

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (stage, value) in enumerate(zip(df[STAGE], df[VALUE], strict=True)):
    y_top = y_edges[i] - gap / 2
    y_bot = y_edges[i + 1] + gap / 2
    w_top = widths[i]
    # Flat bottom on the last segment — trapezoid ends at the actual
    # data width instead of tapering to a decorative point.
    w_bot = widths[i + 1] if i + 1 < n else widths[i]

    y = np.array([y_top, y_bot])
    x_left = np.array([-w_top / 2, -w_bot / 2])
    x_right = np.array([w_top / 2, w_bot / 2])
    ax.fill_betweenx(
        y, x_left, x_right, facecolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], edgecolor=PAGE_BG, linewidth=1
    )

    # The last (narrowest) segment is overflowed by its label, so it takes INK
    # to stay legible on the page background as well as on its own fill.
    label_color = "white" if i + 1 < n else INK
    ax.text(
        0,
        (y_top + y_bot) / 2,
        f"{stage}\n{value:,}  ·  {widths[i] * 100:.0f}%",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=label_color,
    )

# Style
ax.set_xlim(-0.65, 0.65)
ax.set_ylim(-0.2, n + 0.2)
ax.axis("off")
ax.set_title("funnel-basic · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

# Stage index axis on the left
for i in range(n):
    y_mid = (y_edges[i] + y_edges[i + 1]) / 2
    ax.text(-0.62, y_mid, f"Stage {i + 1}", ha="left", va="center", fontsize=9, color=INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
