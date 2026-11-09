"""anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Facial features in mapping order: the i-th variable drives the i-th feature,
# features without a variable stay at their neutral midpoint
FEATURES = ["Face width", "Face height", "Eye size", "Mouth curve", "Eye spacing", "Brow slant", "Nose length"]
FEATURE_INK = "#1A1A17"  # strokes drawn on the face fill, which keeps its color in both themes
EYE_WHITE = "#FFFDF6"

# Columns: set these to your table's column names
CAR = "Car"  # role: observation_id
RATINGS = ["Fuel efficiency", "Power", "Reliability", "Comfort", "Safety", "Cargo space", "Price"]  # role: variable_
CAR_CLASS = "Car class"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("car_ratings.csv")
np.random.seed(42)
class_profiles = {
    "Economy": {
        "models": ["City Hatch", "Compact Sedan", "Eco Wagon"],
        "ratings": [(0.70, 0.25), (0.20, 0.20), (0.40, 0.30), (0.30, 0.30), (0.40, 0.25), (0.55, 0.30), (0.05, 0.20)],
    },
    "Sports": {
        "models": ["Roadster GT", "Track Coupé", "Turbo Spyder"],
        "ratings": [(0.15, 0.20), (0.75, 0.20), (0.40, 0.25), (0.25, 0.25), (0.35, 0.25), (0.05, 0.20), (0.55, 0.25)],
    },
    "Luxury": {
        "models": ["Grand Tourer", "Executive Sedan", "Premium SUV"],
        "ratings": [(0.35, 0.25), (0.50, 0.25), (0.70, 0.25), (0.70, 0.25), (0.70, 0.25), (0.45, 0.40), (0.70, 0.25)],
    },
}
rows = []
for car_class, profile in class_profiles.items():
    for model in profile["models"]:
        ratings = [low + np.random.rand() * span for low, span in profile["ratings"]]
        rows.append({CAR: model, CAR_CLASS: car_class, **dict(zip(RATINGS, ratings, strict=True))})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
values = df[RATINGS].astype(float)
spread = (values.max() - values.min()).replace(0, np.nan)
scaled = ((values - values.min()) / spread).fillna(0.5)  # normalized to 0-1; missing → neutral feature
features = pd.DataFrame(0.5, index=df.index, columns=FEATURES)
mapped = list(zip(FEATURES, RATINGS, strict=False))
for feature, rating in mapped:
    features[feature] = scaled[rating]

# Color by class while the classes fit the palette, otherwise one color for every face
groups = df[CAR_CLASS].dropna().unique()
if len(groups) > len(IMPRINT_PALETTE):
    groups = []
group_colors = dict(zip(groups, IMPRINT_PALETTE, strict=False))

n_cols = int(np.ceil(np.sqrt(len(df))))
n_rows = int(np.ceil(len(df) / n_cols))
col_step = 1.2
row_step = 1.12

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.2)

for pos, (idx, face) in enumerate(features.iterrows()):
    cx = (pos % n_cols) * col_step
    cy = -(pos // n_cols) * row_step
    width = 0.45 + face["Face width"] * 0.35
    height = 0.6 + face["Face height"] * 0.3
    eye = 0.045 + face["Eye size"] * 0.05
    eye_dx = width * (0.15 + face["Eye spacing"] * 0.1)
    eye_y = cy + height * 0.14
    color = group_colors.get(df.at[idx, CAR_CLASS], IMPRINT_PALETTE[0])

    ax.add_patch(patches.Ellipse((cx, cy), width, height, facecolor=color, edgecolor=INK, linewidth=1.4))

    for side in (-1, 1):
        ex = cx + side * eye_dx
        ax.add_patch(
            patches.Ellipse((ex, eye_y), eye * 1.6, eye, facecolor=EYE_WHITE, edgecolor=FEATURE_INK, linewidth=0.9)
        )
        ax.add_patch(patches.Circle((ex, eye_y), eye * 0.32, facecolor=FEATURE_INK))
        brow_y = eye_y + eye * 0.95
        brow_tilt = (face["Brow slant"] - 0.5) * 0.08
        ax.plot(
            [ex - side * eye * 0.8, ex + side * eye * 0.8],
            [brow_y - brow_tilt, brow_y + brow_tilt],
            color=FEATURE_INK,
            linewidth=1.6,
            solid_capstyle="round",
        )

    nose = 0.05 + face["Nose length"] * 0.08
    ax.plot([cx, cx], [cy + nose * 0.3, cy - nose * 0.7], color=FEATURE_INK, linewidth=1.3, solid_capstyle="round")

    mouth_half = width * 0.2
    mouth_x = np.linspace(-mouth_half, mouth_half, 40)
    curve = (face["Mouth curve"] - 0.5) * 0.14
    mouth_y = cy - height * 0.25 - curve * (1 - (mouth_x / mouth_half) ** 2)
    ax.plot(cx + mouth_x, mouth_y, color=FEATURE_INK, linewidth=1.8, solid_capstyle="round")

    ax.text(cx, cy - height / 2 - 0.05, df.at[idx, CAR], ha="center", va="top", fontsize=9, color=INK)

ax.set_xlim(-0.6, (n_cols - 1) * col_step + 0.6)
ax.set_ylim(-(n_rows - 1) * row_step - 0.65, 0.5)
ax.set_aspect("equal")
ax.axis("off")

# Style
title = "Car Ratings · chernoff-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=10, fontweight="bold", color=INK, pad=10)

# Feature key and class legend share one boxed treatment, side by side under the grid
key_handles = [patches.Patch(visible=False) for _ in mapped]
key_labels = [f"{feature}  ←  {rating}" for feature, rating in mapped]
key = fig.legend(
    key_handles,
    key_labels,
    title="Feature key",
    loc="lower left",
    bbox_to_anchor=(0.04, 0.025),
    ncol=2,
    handlelength=0,
    handletextpad=0,
    columnspacing=1.6,
    fontsize=9,
    title_fontsize=9,
    alignment="left",
    frameon=True,
)
legends = [key]

if len(groups) > 0:
    handles = [patches.Patch(facecolor=group_colors[g], edgecolor=INK, linewidth=0.8, label=g) for g in groups]
    legends.append(
        fig.legend(
            handles=handles,
            title=CAR_CLASS,
            loc="lower right",
            bbox_to_anchor=(0.96, 0.025),
            fontsize=9,
            title_fontsize=9,
            alignment="left",
            frameon=True,
        )
    )

for leg in legends:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    leg.get_title().set_color(INK)
    leg.get_title().set_fontweight("bold")

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
