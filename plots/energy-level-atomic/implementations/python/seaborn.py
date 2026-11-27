"""anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Seaborn theme — theme-adaptive chrome
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
UV_MAX_NM = 400  # emission below this wavelength is ultraviolet
VISIBLE_MAX_NM = 700  # up to this wavelength it is visible light, beyond it infrared

# Columns: set these to your table's column names
UPPER = "Upper level"  # role: level
ENERGY = "Upper energy (eV)"  # role: energy
LOWER = "Lower level"  # role: extra
LOWER_ENERGY = "Lower energy (eV)"  # role: extra
SERIES = "Series"  # role: transitions
WAVELENGTH = "Wavelength (nm)"  # role: extra

# Data: replace this block with your own table, one row per transition, for example df = pd.read_csv("transitions.csv")
# Hydrogen atom, E_n = -13.6 / n² eV; emission from the upper to the lower level
transitions = [
    (2, 1, "Lyman", 122),
    (3, 1, "Lyman", 103),
    (4, 1, "Lyman", 97),
    (3, 2, "Balmer", 656),
    (4, 2, "Balmer", 486),
    (5, 2, "Balmer", 434),
    (4, 3, "Paschen", 1875),
    (5, 3, "Paschen", 1282),
    (6, 3, "Paschen", 1094),
]
df = pd.DataFrame(transitions, columns=["upper_n", "lower_n", SERIES, WAVELENGTH])
df[ENERGY] = (-13.6 / df["upper_n"] ** 2).round(2)
df[LOWER_ENERGY] = (-13.6 / df["lower_n"] ** 2).round(2)
df[UPPER] = "n=" + df["upper_n"].astype(str)
df[LOWER] = "n=" + df["lower_n"].astype(str)
df = df[[UPPER, ENERGY, LOWER, LOWER_ENERGY, SERIES, WAVELENGTH]]

# Plot: reads only df and the constants above
# Transitions without both energies cannot be placed
df = df.dropna(subset=[ENERGY, LOWER_ENERGY, WAVELENGTH]).reset_index(drop=True)
# Every distinct level once, lowest energy first
levels = (
    pd.concat(
        [
            df[[UPPER, ENERGY]].set_axis(["level", "energy"], axis=1),
            df[[LOWER, LOWER_ENERGY]].set_axis(["level", "energy"], axis=1),
        ]
    )
    .drop_duplicates("level")
    .sort_values("energy")
    .reset_index(drop=True)
)

# Levels sit at their energy; the y axis is symlog so the converging upper levels stay readable
ION_E = 0.0  # ionization limit in eV
visual_y = dict(zip(levels["level"], levels["energy"], strict=True))
energy_of = visual_y
df["y_top"] = df[ENERGY]
df["y_bot"] = df[LOWER_ENERGY]

# Series colors from Imprint palette — CVD-safe canonical order
series_names = list(df[SERIES].unique())
series_colors = {name: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, name in enumerate(series_names)}


def spectral_region(wavelength):
    """Name of the spectral region a wavelength in nm falls in."""
    if wavelength < UV_MAX_NM:
        return "ultraviolet"
    return "visible" if wavelength <= VISIBLE_MAX_NM else "infrared"


# Subtle background column tints — seaborn palette functions (light/dark adaptive)
series_bg = {}
for name, color in series_colors.items():
    if THEME == "light":
        series_bg[name] = sns.light_palette(color, n_colors=8)[1]
    else:
        series_bg[name] = sns.dark_palette(color, n_colors=8, reverse=True)[1]

# Schematic x layout: arrows of one series side by side, a wider gap between series
ARROW_STEP, SERIES_GAP, X_START = 0.14, 0.10, 0.12
x_cursor = X_START
for series in series_names:
    mask = df[SERIES] == series
    df.loc[mask, "x_pos"] = x_cursor + ARROW_STEP * np.arange(mask.sum())
    x_cursor += ARROW_STEP * (mask.sum() - 1) + SERIES_GAP

# Figure — canvas: 3200 × 1800 px (16:9 landscape)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
# Reserve right margin for energy value labels (clip_on=False text extends here)
fig.subplots_adjust(left=0.105, right=0.80, top=0.92, bottom=0.07)
ax.set_yscale("symlog", linthresh=0.1, linscale=0.4)
ax.set_ylim(df[LOWER_ENERGY].min() * 1.1, ION_E + 0.25)

line_xmin, line_xmax = 0.03, 1.22

# Background column tints
for series in series_names:
    x_pos = df.loc[df[SERIES] == series, "x_pos"]
    alpha = 0.12 if THEME == "light" else 0.10
    ax.axvspan(x_pos.min() - 0.028, x_pos.max() + 0.042, alpha=alpha, color=series_bg[series], zorder=0)

# Energy level lines via sns.lineplot (DataFrame-driven)
level_df = pd.concat(
    [
        pd.DataFrame({"x": line_xmin, "y": levels["energy"], "level": levels["level"]}),
        pd.DataFrame({"x": line_xmax, "y": levels["energy"], "level": levels["level"]}),
    ]
)

sns.lineplot(
    data=level_df, x="x", y="y", units="level", estimator=None, color=INK, linewidth=2.0, ax=ax, legend=False, zorder=3
)

# Level endpoints via sns.scatterplot
sns.scatterplot(data=level_df, x="x", y="y", color=INK, s=25, zorder=4, ax=ax, legend=False, edgecolor="none")

# Energy value labels — clip_on=False so text extends into right margin
for label, y_pos in visual_y.items():
    ax.text(
        line_xmax + 0.018,
        y_pos,
        f"{label}  ({energy_of[label]:.2f} eV)",
        fontsize=9,
        va="center",
        ha="left",
        color=INK,
        fontweight="medium",
        clip_on=False,
    )

# Ionization limit (dashed reference line) at 0 eV
ax.hlines(ION_E, line_xmin, line_xmax, colors=INK_SOFT, linewidth=1.5, linestyles="dashed", zorder=3)
ax.text(
    line_xmax + 0.018,
    ION_E,
    "Ionization  (0.00 eV)",
    fontsize=9,
    va="center",
    ha="left",
    color=INK_SOFT,
    fontweight="medium",
    clip_on=False,
)


# Transition arrows (emission: downward); each wavelength label sits in the widest open span of its arrow
def to_px(energy):
    """Display y of an energy on the current axis."""
    return ax.transData.transform((0, energy))[1]


level_energies = sorted(visual_y.values())
for _, row in df.iterrows():
    color = series_colors[row[SERIES]]
    ax.annotate(
        "",
        xy=(row["x_pos"], row["y_bot"]),
        xytext=(row["x_pos"], row["y_top"]),
        arrowprops={
            "arrowstyle": "->,head_width=0.28,head_length=0.18",
            "color": color,
            "linewidth": 1.8,
            "shrinkA": 2,
            "shrinkB": 2,
        },
        zorder=2,
    )
    spans = [
        (lo, hi)
        for lo, hi in zip(level_energies[:-1], level_energies[1:], strict=True)
        if lo >= row["y_bot"] and hi <= row["y_top"]
    ]
    lo, hi = max(spans or [(row["y_bot"], row["y_top"])], key=lambda span: to_px(span[1]) - to_px(span[0]))
    mid_y = ax.transData.inverted().transform((0, (to_px(lo) + to_px(hi)) / 2))[1]
    ax.text(
        row["x_pos"],
        mid_y,
        f"{row[WAVELENGTH]} nm",
        fontsize=8,
        color=color,
        va="center",
        ha="center",
        zorder=5,
        bbox={"facecolor": PAGE_BG, "edgecolor": "none", "pad": 1.0},
    )

# Series labels and spectral region subtitles
for series in series_names:
    rows = df[df[SERIES] == series]
    x_center = rows["x_pos"].mean()
    color = series_colors[series]
    ax.text(
        x_center,
        0.965,
        f"{series} series",
        fontsize=9,
        fontweight="bold",
        ha="center",
        color=color,
        transform=ax.get_xaxis_transform(),
    )
    ax.text(
        x_center,
        0.925,
        f"({spectral_region(float(rows[WAVELENGTH].astype(float).median()))})",
        transform=ax.get_xaxis_transform(),
        fontsize=8,
        ha="center",
        color=color,
        style="italic",
    )

# Axes: energy in eV on a symlog scale, ticks that show it
ax.set_xlim(0, 1.25)
ax.set_yticks([-13.6, -10, -5, -2, -1, -0.5, 0])
ax.set_yticklabels(["−13.6", "−10", "−5", "−2", "−1", "−0.5", "0"])
ax.yaxis.set_minor_locator(plt.NullLocator())
ax.tick_params(axis="y", labelsize=9, length=4)
ax.set_ylabel("Energy (eV, symlog scale)", fontsize=9)

title = "energy-level-atomic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", pad=10, color=INK)
ax.set_xticks([])
ax.set_xlabel("")
sns.despine(ax=ax, bottom=True)

# Save — no bbox_inches so canvas stays at exactly 3200 × 1800
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
