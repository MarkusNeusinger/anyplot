"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-04-26
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Polygon


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data — sales funnel from specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]
max_value = values[0]
percentages = [v / max_value * 100 for v in values]

# Seaborn theme (chrome only — funnel polygons drawn directly)
sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Funnel geometry
n_stages = len(stages)
funnel_height = 0.78
stage_gap = 0.015
stage_height = (funnel_height - (n_stages - 1) * stage_gap) / n_stages
center_x = 0.55  # shift right to leave room for stage names on left
max_width = 0.55

# Draw trapezoidal segments
for i in range(n_stages):
    top_width = values[i] / max_value * max_width
    if i < n_stages - 1:
        bottom_width = values[i + 1] / max_value * max_width
    else:
        bottom_width = top_width * 0.6

    y_top = 1 - 0.12 - i * (stage_height + stage_gap)
    y_bottom = y_top - stage_height

    vertices = [
        (center_x - top_width / 2, y_top),
        (center_x + top_width / 2, y_top),
        (center_x + bottom_width / 2, y_bottom),
        (center_x - bottom_width / 2, y_bottom),
    ]
    trapezoid = Polygon(vertices, facecolor=OKABE_ITO[i], edgecolor=PAGE_BG, linewidth=3, closed=True)
    ax.add_patch(trapezoid)

    center_y = (y_top + y_bottom) / 2

    # Stage name on the left (fixed x to avoid collision with value text in narrow segments)
    ax.text(0.20, center_y, stages[i], ha="right", va="center", fontsize=20, fontweight="medium", color=INK)

    # Value + percentage centered on the segment. Path-effect stroke keeps the white
    # text readable when narrow segments force it to overflow onto the page background.
    value_text = ax.text(
        center_x,
        center_y,
        f"{values[i]:,} ({percentages[i]:.0f}%)",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#FFFFFF",
    )
    value_text.set_path_effects([pe.withStroke(linewidth=2.5, foreground=OKABE_ITO[i])])

    # Conversion rate between stages — placed inside the gap, right of the funnel
    if i < n_stages - 1:
        conversion_rate = values[i + 1] / values[i] * 100
        ax.text(
            center_x + max_width / 2 + 0.04,
            y_bottom - stage_gap / 2,
            f"↓ {conversion_rate:.0f}%",
            ha="left",
            va="center",
            fontsize=14,
            color=INK_MUTED,
            style="italic",
        )

# Axis frame
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("funnel-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
