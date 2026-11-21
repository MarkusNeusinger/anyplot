"""anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-15
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import to_rgb
from sklearn.datasets import load_wine


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Seaborn setup
sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
OBSERVATION = "Observation"  # role: observation_id
WINE_CLASS = "Wine class"  # role: extra
ALCOHOL = "Alcohol"  # role: variable_
PHENOLS = "Total phenols"  # role: variable_
COLOR_INTENSITY = "Color intensity"  # role: variable_
PROLINE = "Proline"  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("observations.csv")
np.random.seed(42)
wine = load_wine()
wine_table = pd.DataFrame(wine.data, columns=wine.feature_names)
picked = np.concatenate([np.random.choice(np.where(wine.target == cls)[0], size=5, replace=False) for cls in range(3)])
df = pd.DataFrame(
    {
        OBSERVATION: [f"Class {wine.target[i] + 1} #{n % 5 + 1}" for n, i in enumerate(picked)],
        WINE_CLASS: [f"Class {wine.target[i] + 1}" for i in picked],
        ALCOHOL: wine_table["alcohol"].to_numpy()[picked],
        PHENOLS: wine_table["total_phenols"].to_numpy()[picked],
        COLOR_INTENSITY: wine_table["color_intensity"].to_numpy()[picked],
        PROLINE: wine_table["proline"].to_numpy()[picked],
    }
)

# Plot: reads only df and the constants above
features = [ALCOHOL, PHENOLS, COLOR_INTENSITY, PROLINE]
spans = df.groupby(WINE_CLASS, sort=False)[features].transform(lambda s: s.max() - s.min())
mins = df.groupby(WINE_CLASS, sort=False)[features].transform("min")
norm = ((df[features] - mins) / spans.where(spans > 0, 1.0)).to_numpy()

codes, groups = pd.factorize(df[WINE_CLASS])
face_colors = [IMPRINT_PALETTE[c % len(IMPRINT_PALETTE)] for c in codes]

n_faces = len(df)
n_cols = 5
n_rows = int(np.ceil(n_faces / n_cols))

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(n_rows, n_cols, hspace=0.3, wspace=0.1, left=0.03, right=0.97, top=0.88, bottom=0.12)

for idx in range(n_faces):
    ax = fig.add_subplot(gs[idx // n_cols, idx % n_cols])
    f = norm[idx]
    color = face_colors[idx]

    # Feature mapping: width <- alcohol, height <- phenols, eye size <- color intensity, mouth <- proline
    face_width = 0.45 + f[0] * 0.55
    face_height = 0.55 + f[1] * 0.55
    eye_size = 0.04 + f[2] * 0.12
    mouth_curve = -0.35 + f[3] * 0.7

    ax.add_patch(
        mpatches.Ellipse((0.5, 0.5), face_width, face_height, facecolor=color, edgecolor=INK, linewidth=1.3, alpha=0.9)
    )

    eye_y = 0.58
    eye_spacing = 0.11 + f[1] * 0.05
    for sign in (-1, 1):
        ex = 0.5 + sign * eye_spacing
        ax.add_patch(
            mpatches.Ellipse((ex, eye_y), eye_size * 1.6, eye_size, facecolor=ELEVATED_BG, edgecolor=INK, linewidth=1.0)
        )
        ax.add_patch(mpatches.Circle((ex, eye_y), eye_size * 0.35, facecolor=INK))

    # Eyebrows slant with eye size
    slant = -0.12 + f[2] * 0.24
    brow_y = eye_y + eye_size + 0.05
    for sign in (-1, 1):
        ex = 0.5 + sign * eye_spacing
        ax.plot(
            [ex - 0.05, ex + 0.05],
            [brow_y + sign * slant, brow_y - sign * slant],
            color=INK,
            linewidth=1.8,
            solid_capstyle="round",
        )

    # Nose, a darker shade of the face color
    nose_size = 0.03 + f[0] * 0.025
    nose_color = tuple(0.7 * c for c in to_rgb(color))
    ax.add_patch(
        mpatches.Polygon(
            [[0.5, 0.50], [0.5 - nose_size, 0.40], [0.5 + nose_size, 0.40]],
            facecolor=nose_color,
            edgecolor=INK,
            linewidth=0.8,
        )
    )

    # Mouth
    mouth_width = 0.08 + f[0] * 0.05
    mx = np.linspace(0.5 - mouth_width, 0.5 + mouth_width, 25)
    my = 0.30 + mouth_curve * (mx - 0.5) ** 2 * 18
    ax.plot(mx, my, color=INK_SOFT, linewidth=1.8, solid_capstyle="round")

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0.5, -0.1, df[OBSERVATION].iloc[idx], ha="center", va="top", fontsize=7, fontweight="bold", color=INK)

# Style
fig.suptitle("chernoff-basic · python · seaborn · anyplot.ai", fontsize=13, fontweight="medium", y=0.97, color=INK)

legend_handles = [
    mpatches.Patch(facecolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], edgecolor=INK, linewidth=0.8, label=g)
    for i, g in enumerate(groups)
]
fig.legend(
    handles=legend_handles,
    loc="upper right",
    fontsize=7,
    title=WINE_CLASS,
    title_fontsize=7,
    frameon=True,
    bbox_to_anchor=(0.995, 0.995),
)

key = (
    f"Face width ← {ALCOHOL}  |  Face height ← {PHENOLS}  |  "
    f"Eye size ← {COLOR_INTENSITY}  |  Mouth curve ← {PROLINE}  (each scaled 0–1 within class)"
)
fig.text(0.03, 0.03, key, ha="left", va="center", fontsize=6.5, style="italic", color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
