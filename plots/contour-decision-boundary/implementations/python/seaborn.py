"""anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap
from sklearn.neighbors import KNeighborsClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
STATES = ["Healthy", "Degrading", "Faulty"]  # ordered machine health states
N_NEIGHBORS = 15  # k of the nearest-neighbor classifier
MESH_STEPS = 300  # mesh resolution per axis
CORRECT, MISCLASSIFIED = "Correct", "Misclassified"  # marker styles

# Columns: set these to your table's column names
VIBRATION = "Vibration (mm/s)"  # role: X1
TEMPERATURE = "Bearing temperature (°C)"  # role: X2
STATE = "Health state"  # role: y
FIT = "Prediction"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("machines.csv")
rng = np.random.default_rng(7)
centers = np.array([[2.0, 55.0], [3.9, 66.0], [5.8, 77.0]])
spread = np.array([[1.1, 5.0], [1.2, 5.5], [1.1, 5.0]])  # (vibration, temperature) std per state
labels = np.repeat(np.arange(len(STATES)), 90)
blobs = centers[labels] + rng.normal(size=(len(labels), 2)) * spread[labels]
df = pd.DataFrame(
    {VIBRATION: np.round(blobs[:, 0], 2), TEMPERATURE: np.round(blobs[:, 1], 1), STATE: [STATES[i] for i in labels]}
)

# Plot: reads only df and the constants above
df = df.dropna(subset=[VIBRATION, TEMPERATURE, STATE]).astype({STATE: str}).reset_index(drop=True)
states = list(dict.fromkeys(df[STATE]))
state_colors = {s: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, s in enumerate(states)}

features = df[[VIBRATION, TEMPERATURE]].to_numpy()
scale = features.std(axis=0)
clf = KNeighborsClassifier(n_neighbors=N_NEIGHBORS).fit(features / scale, df[STATE])
correct = clf.predict(features / scale) == df[STATE].to_numpy()
df[FIT] = np.where(correct, CORRECT, MISCLASSIFIED)

pad = 0.08 * np.ptp(features, axis=0)
lo, hi = features.min(axis=0) - pad, features.max(axis=0) + pad
xx, yy = np.meshgrid(np.linspace(lo[0], hi[0], MESH_STEPS), np.linspace(lo[1], hi[1], MESH_STEPS))
region = clf.predict(np.c_[xx.ravel(), yy.ravel()] / scale)
region_idx = np.array([states.index(s) for s in region]).reshape(xx.shape)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

region_cmap = ListedColormap([state_colors[s] for s in states])
ax.contourf(xx, yy, region_idx, levels=np.arange(len(states) + 1) - 0.5, cmap=region_cmap, alpha=0.22)
ax.contour(xx, yy, region_idx, levels=np.arange(len(states) - 1) + 0.5, colors=INK_SOFT, linewidths=1.2)

sns.scatterplot(
    data=df,
    x=VIBRATION,
    y=TEMPERATURE,
    hue=STATE,
    hue_order=states,
    palette=state_colors,
    style=FIT,
    style_order=[CORRECT, MISCLASSIFIED],
    markers={CORRECT: "o", MISCLASSIFIED: "X"},
    s=38,
    edgecolor=INK,
    linewidth=0.5,
    ax=ax,
)

# Style
ax.set_xlim(lo[0], hi[0])
ax.set_ylim(lo[1], hi[1])
accuracy = correct.mean() * 100
ax.set_title("contour-decision-boundary · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.set_xlabel(VIBRATION, fontsize=10)
ax.set_ylabel(TEMPERATURE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.legend(fontsize=7, title_fontsize=7.5, loc="upper left", framealpha=0.95, title=f"k-NN accuracy {accuracy:.1f}%")
sns.despine(ax=ax)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
