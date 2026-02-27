"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 79/100 | Created: 2026-02-27
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Seaborn theming
sns.set_style("white")
sns.set_context("talk", font_scale=1.2)

# Data — Hydrogen atom energy levels E_n = -13.6 / n² eV
energy_values = {"n=1": -13.60, "n=2": -3.40, "n=3": -1.51, "n=4": -0.85, "n=5": -0.54, "n=6": -0.38}

# Visual y-positions (qualitative spacing so upper levels remain readable)
visual_y = {"n=1": 0.0, "n=2": 3.5, "n=3": 5.5, "n=4": 7.0, "n=5": 8.2, "n=6": 9.2}
ionization_y = 10.5

# Spectral series transitions (upper → lower = emission)
transitions = [
    ("n=2", "n=1", "Lyman", 122),
    ("n=3", "n=1", "Lyman", 103),
    ("n=4", "n=1", "Lyman", 97),
    ("n=3", "n=2", "Balmer", 656),
    ("n=4", "n=2", "Balmer", 486),
    ("n=5", "n=2", "Balmer", 434),
    ("n=4", "n=3", "Paschen", 1875),
    ("n=5", "n=3", "Paschen", 1282),
    ("n=6", "n=3", "Paschen", 1094),
]

# Colors per series (spectrum-inspired: UV=purple, visible=blue, IR=red)
series_palette = sns.color_palette(["#7B2FBE", "#306998", "#C0392B"])
series_names = ["Lyman", "Balmer", "Paschen"]
series_colors = dict(zip(series_names, series_palette, strict=True))

# X positions for each series column
series_x_base = {"Lyman": 0.18, "Balmer": 0.42, "Paschen": 0.64}
arrow_spacing = 0.045

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

line_xmin = 0.06
line_xmax = 0.84

# Build DataFrame for energy level endpoints and plot with sns.scatterplot
level_rows = []
for label, y_pos in visual_y.items():
    level_rows.append({"x": line_xmin, "y": y_pos, "level": label})
    level_rows.append({"x": line_xmax, "y": y_pos, "level": label})
level_df = pd.DataFrame(level_rows)

# Use sns.lineplot to draw each energy level as a horizontal line
for label in visual_y:
    subset = level_df[level_df["level"] == label]
    sns.lineplot(data=subset, x="x", y="y", color="#2C3E50", linewidth=2.5, ax=ax, legend=False, zorder=3)

# Mark level endpoints with sns.scatterplot
sns.scatterplot(data=level_df, x="x", y="y", color="#2C3E50", s=40, zorder=4, ax=ax, legend=False, edgecolor="none")

# Energy value labels on the right
for label, y_pos in visual_y.items():
    energy = energy_values[label]
    ax.text(
        line_xmax + 0.015,
        y_pos,
        f"{label}   ({energy:.2f} eV)",
        fontsize=18,
        va="center",
        ha="left",
        color="#2C3E50",
        fontweight="medium",
    )

# Ionization limit (dashed)
ax.hlines(ionization_y, line_xmin, line_xmax, colors="#888888", linewidth=2, linestyles="dashed", zorder=3)
ax.text(
    line_xmax + 0.015,
    ionization_y,
    "Ionization  (0.00 eV)",
    fontsize=18,
    va="center",
    ha="left",
    color="#888888",
    fontweight="medium",
)

# Draw transition arrows
for upper, lower, series, wavelength_nm in transitions:
    y_top = visual_y[upper]
    y_bot = visual_y[lower]
    color = series_colors[series]

    series_transitions = [t for t in transitions if t[2] == series]
    idx = next(i for i, t in enumerate(series_transitions) if t[0] == upper and t[1] == lower)
    x_pos = series_x_base[series] + idx * arrow_spacing

    gap = 0.18
    ax.annotate(
        "",
        xy=(x_pos, y_bot + gap),
        xytext=(x_pos, y_top - gap),
        arrowprops={"arrowstyle": "->,head_width=0.35,head_length=0.22", "color": color, "linewidth": 2.2},
        zorder=2,
    )

    # Wavelength label (rotated 90° to avoid overlap)
    mid_y = (y_top + y_bot) / 2
    ax.text(
        x_pos + 0.012,
        mid_y,
        f"{wavelength_nm} nm",
        fontsize=13,
        color=color,
        va="center",
        ha="left",
        rotation=90,
        alpha=0.85,
    )

# Series labels at top
for series, x_base in series_x_base.items():
    x_center = x_base + arrow_spacing
    ax.text(
        x_center,
        ionization_y + 0.7,
        f"{series} series",
        fontsize=18,
        fontweight="bold",
        ha="center",
        color=series_colors[series],
    )

# Energy direction arrow on left
ax.annotate(
    "", xy=(0.02, 11.0), xytext=(0.02, -0.5), arrowprops={"arrowstyle": "-|>", "color": "#999999", "linewidth": 1.5}
)
ax.text(0.025, 5.25, "Energy", fontsize=20, rotation=90, va="center", ha="left", color="#999999")

# Style — use seaborn's despine for clean removal
ax.set_xlim(-0.01, 1.15)
ax.set_ylim(-1.0, 12.0)
ax.set_title("energy-level-atomic · seaborn · pyplots.ai", fontsize=26, fontweight="medium", pad=20)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
sns.despine(ax=ax, left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
