""" anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-27
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
LEVEL_COLOR = IMPRINT_PALETTE[2]  # Imprint blue for the level lines

# Constants
IONIZATION = 0.0  # energy (eV) of the ionization limit
HC_EV_NM = 1239.84  # h*c in eV*nm, converts a transition energy to its wavelength
# Semantic exception: Balmer lines take the colour of their visible wavelength, red to violet
SPECTRAL = ["#AE3030", "#2ABCCD", "#C475FD", "#954477"]
GREEK = "αβγδεζηθ"
REGION = {"Lyman": "UV", "Balmer": "Visible"}  # spectral region of the known series

# Columns: set these to your table's column names
SERIES = "Series"  # role: extra
UPPER = "Upper level"  # role: level
LOWER = "Lower level"  # role: extra
UPPER_ENERGY = "Upper energy (eV)"  # role: energy
LOWER_ENERGY = "Lower energy (eV)"  # role: extra

# Data: hydrogen atom, E_n = -13.6 / n^2 (eV); one row per transition.
# Replace this block with your own table, for example df = pd.read_csv("transitions.csv")
transitions = [("Lyman", upper, 1) for upper in range(2, 7)] + [("Balmer", upper, 2) for upper in range(3, 7)]
df = pd.DataFrame(
    {
        SERIES: [series for series, _, _ in transitions],
        UPPER: [f"n = {upper}" for _, upper, _ in transitions],
        LOWER: [f"n = {lower}" for _, _, lower in transitions],
        UPPER_ENERGY: [-13.6 / upper**2 for _, upper, _ in transitions],
        LOWER_ENERGY: [-13.6 / lower**2 for _, _, lower in transitions],
    }
)

# Plot: reads only df and the constants above
df = df.dropna()
# Levels: every distinct level of the table, lowest energy first
levels = pd.concat(
    [
        df[[UPPER, UPPER_ENERGY]].set_axis(["level", "energy"], axis=1),
        df[[LOWER, LOWER_ENERGY]].set_axis(["level", "energy"], axis=1),
    ]
).drop_duplicates("level")
levels = levels.sort_values("energy").reset_index(drop=True)

# Sqrt-compressed display positions: y = -sqrt(|E|) keeps the order and spreads the upper levels
levels["y"] = -np.sqrt(np.abs(levels["energy"] - IONIZATION))
y_of = dict(zip(levels["level"], levels["y"], strict=True))
ion_y = 0.0
n_levels = len(levels)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

left, right = 0.18, 0.82
gap = 0.06  # arrow gap from level lines

# Energy level lines, quantum labels and energy values
for rank, row in levels.iterrows():
    lw = 3.5 if rank == 0 else 2.5  # bolder ground state anchors the diagram
    ax.plot([left, right], [row["y"], row["y"]], color=LEVEL_COLOR, linewidth=lw, solid_capstyle="round", zorder=3)
    ax.text(
        right + 0.02, row["y"], row["level"], fontsize=8, va="center", ha="left", color=LEVEL_COLOR, fontweight="medium"
    )
    # Upper levels crowd together: smaller font + stagger the second-highest level for separation
    label_fs = 8 if rank < 3 else 7
    label_x = (left - 0.05) if rank == n_levels - 2 else (left - 0.02)
    ax.text(label_x, row["y"], f"{row['energy']:.2f} eV", fontsize=label_fs, va="center", ha="right", color=INK_MUTED)

# Ionization limit (dashed, theme-adaptive)
ax.plot([left, right], [ion_y, ion_y], color=INK_SOFT, linewidth=1.5, linestyle="--", zorder=2)
ax.text(right + 0.02, ion_y, f"Ionization ({IONIZATION:g} eV)", fontsize=8, va="center", ha="left", color=INK_SOFT)

# Transition arrows: one column band per series, Lyman left and Balmer right
series_names = list(dict.fromkeys(df[SERIES]))
legend_handles = []
for s, name in enumerate(series_names):
    rows = df[df[SERIES] == name]
    x_start = 0.24 + 0.31 * min(s, 1)
    xs = np.linspace(x_start, x_start + 0.16, len(rows)) if len(rows) > 1 else np.array([x_start + 0.08])
    for k, ((_, row), xp) in enumerate(zip(rows.iterrows(), xs, strict=True)):
        if s == 0:
            color = IMPRINT_PALETTE[0]
        else:
            color = SPECTRAL[k] if k < len(SPECTRAL) else IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)]
            wavelength = HC_EV_NM / (row[UPPER_ENERGY] - row[LOWER_ENERGY])
            legend_handles.append(mpatches.Patch(color=color, label=f"H-{GREEK[k % len(GREEK)]}  {wavelength:.0f} nm"))
        ax.annotate(
            "",
            xy=(xp, y_of[row[LOWER]] + gap),
            xytext=(xp, y_of[row[UPPER]] - gap),
            arrowprops={"arrowstyle": "->,head_width=0.3,head_length=0.15", "color": color, "lw": 2.2},
            zorder=4,
        )
    # Series label beside the band, level-wise between the first arrow's two ends
    region = f"\n({REGION[name]})" if name in REGION else ""
    label_color = IMPRINT_PALETTE[0] if s == 0 else SPECTRAL[1 % len(SPECTRAL)]
    first = rows.iloc[0]
    ax.text(
        xs.max() + 0.03,
        (y_of[first[LOWER]] + y_of[first[UPPER]]) / 2,
        f"{name} series{region}",
        fontsize=8,
        ha="left",
        va="center",
        color=label_color,
        fontstyle="italic",
    )
    if s == 0:
        legend_handles.append(mpatches.Patch(color=IMPRINT_PALETTE[0], label=f"{name}{region.replace(chr(10), ' ')}"))

# Legend for Balmer transition colors + Lyman
leg = ax.legend(handles=legend_handles, fontsize=8, loc="lower right", fancybox=False)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
title = "energy-level-atomic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_ylabel("Energy (eV)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)
ax.set_xlim(0.05, 1.08)
ax.set_ylim(levels["y"].min() - 0.3, ion_y + 0.4)
ax.set_xticks([])

# Custom y-ticks: real energy values mapped onto the compressed display axis
e_min = levels["energy"].min()
powers = 2.0 ** np.arange(-1, int(np.log2(abs(e_min))) + 1)
tick_energies = np.concatenate([[IONIZATION], IONIZATION - powers, [np.round(e_min)]])
tick_y = -np.sqrt(np.abs(tick_energies - IONIZATION))
ax.set_yticks(tick_y)
ax.set_yticklabels([f"{e:g}" for e in tick_energies])
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
