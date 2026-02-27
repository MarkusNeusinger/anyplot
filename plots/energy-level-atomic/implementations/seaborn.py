""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-27
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Seaborn theming — sns.set_theme (modern comprehensive API)
sns.set_theme(
    style="white", context="talk", font_scale=1.3, rc={"axes.facecolor": "#FAFBFC", "figure.facecolor": "#FFFFFF"}
)

# Data — Hydrogen atom energy levels E_n = -13.6 / n² eV
energy_values = {"n=1": -13.60, "n=2": -3.40, "n=3": -1.51, "n=4": -0.85, "n=5": -0.54, "n=6": -0.38}

# Visual y-positions (qualitative spacing so upper levels remain readable)
visual_y = {"n=1": 0.0, "n=2": 3.5, "n=3": 5.5, "n=4": 7.0, "n=5": 8.2, "n=6": 9.2}
ionization_y = 10.5

# Spectral series transitions (upper → lower = emission)
transition_data = [
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

# Build transition DataFrame for data-driven plotting
transition_df = pd.DataFrame(transition_data, columns=["upper", "lower", "series", "wavelength_nm"])
transition_df["y_top"] = transition_df["upper"].map(visual_y)
transition_df["y_bot"] = transition_df["lower"].map(visual_y)

# Colors — improved luminance contrast for deuteranopia accessibility
# Lyman: bright warm purple (lighter), Balmer: dark blue, Paschen: warm red
series_names = ["Lyman", "Balmer", "Paschen"]
series_palette = sns.color_palette(["#A855F7", "#306998", "#C0392B"])
series_colors = dict(zip(series_names, series_palette, strict=True))

# Distinctive seaborn feature: sns.light_palette for subtle background tints
series_bg = {name: sns.light_palette(color, n_colors=8)[1] for name, color in series_colors.items()}

# X positions for each series column
series_x_base = {"Lyman": 0.18, "Balmer": 0.42, "Paschen": 0.64}
arrow_spacing = 0.048

# Compute x positions per series group in DataFrame
for series in series_names:
    mask = transition_df["series"] == series
    transition_df.loc[mask, "x_pos"] = [series_x_base[series] + i * arrow_spacing for i in range(mask.sum())]

# Figure
fig, ax = plt.subplots(figsize=(16, 9))
line_xmin = 0.06
line_xmax = 0.84

# Subtle background bands for series columns (seaborn light_palette tints)
for series, x_base in series_x_base.items():
    n_trans = (transition_df["series"] == series).sum()
    band_left = x_base - 0.028
    band_right = x_base + (n_trans - 1) * arrow_spacing + 0.038
    ax.axvspan(band_left, band_right, alpha=0.12, color=series_bg[series], zorder=0)

# Build DataFrame for energy level endpoints
level_rows = []
for label, y_pos in visual_y.items():
    level_rows.append({"x": line_xmin, "y": y_pos, "level": label})
    level_rows.append({"x": line_xmax, "y": y_pos, "level": label})
level_df = pd.DataFrame(level_rows)

# Draw each energy level as a horizontal line with sns.lineplot
for label in visual_y:
    subset = level_df[level_df["level"] == label]
    sns.lineplot(data=subset, x="x", y="y", color="#2C3E50", linewidth=2.5, ax=ax, legend=False, zorder=3)

# Mark level endpoints with sns.scatterplot
sns.scatterplot(data=level_df, x="x", y="y", color="#2C3E50", s=50, zorder=4, ax=ax, legend=False, edgecolor="none")

# Energy value labels — 20pt for legibility at 4800×2700
for label, y_pos in visual_y.items():
    energy = energy_values[label]
    ax.text(
        line_xmax + 0.015,
        y_pos,
        f"{label}   ({energy:.2f} eV)",
        fontsize=20,
        va="center",
        ha="left",
        color="#2C3E50",
        fontweight="medium",
    )

# Ionization limit (dashed) — 20pt
ax.hlines(ionization_y, line_xmin, line_xmax, colors="#888888", linewidth=2, linestyles="dashed", zorder=3)
ax.text(
    line_xmax + 0.015,
    ionization_y,
    "Ionization  (0.00 eV)",
    fontsize=20,
    va="center",
    ha="left",
    color="#888888",
    fontweight="medium",
)

# Draw transition arrows from DataFrame
gap = 0.18
for _, row in transition_df.iterrows():
    color = series_colors[row["series"]]
    ax.annotate(
        "",
        xy=(row["x_pos"], row["y_bot"] + gap),
        xytext=(row["x_pos"], row["y_top"] - gap),
        arrowprops={"arrowstyle": "->,head_width=0.35,head_length=0.22", "color": color, "linewidth": 2.2},
        zorder=2,
    )
    # Wavelength label (rotated 90°) — 16pt
    mid_y = (row["y_top"] + row["y_bot"]) / 2
    ax.text(
        row["x_pos"] + 0.014,
        mid_y,
        f"{row['wavelength_nm']} nm",
        fontsize=16,
        color=color,
        va="center",
        ha="left",
        rotation=90,
        alpha=0.9,
    )

# Series labels at top — 20pt with spectral region subtitle for storytelling
spectral_regions = {"Lyman": "ultraviolet", "Balmer": "visible", "Paschen": "infrared"}
for series, x_base in series_x_base.items():
    x_center = x_base + arrow_spacing
    ax.text(
        x_center,
        ionization_y + 0.85,
        f"{series} series",
        fontsize=20,
        fontweight="bold",
        ha="center",
        color=series_colors[series],
    )
    ax.text(
        x_center,
        ionization_y + 0.22,
        f"({spectral_regions[series]})",
        fontsize=14,
        ha="center",
        color=series_colors[series],
        alpha=0.65,
        style="italic",
    )

# Energy direction arrow on left
ax.annotate(
    "", xy=(0.02, 10.8), xytext=(0.02, -0.3), arrowprops={"arrowstyle": "-|>", "color": "#999999", "linewidth": 1.5}
)
ax.text(0.025, 5.25, "Energy", fontsize=20, rotation=90, va="center", ha="left", color="#999999")

# Axes cleanup with sns.despine
ax.set_xlim(-0.01, 1.15)
ax.set_ylim(-0.5, 12.2)
ax.set_title("energy-level-atomic · seaborn · pyplots.ai", fontsize=26, fontweight="medium", pad=20)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
sns.despine(ax=ax, left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
