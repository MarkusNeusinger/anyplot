""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Company market values by sector (billions USD)
sectors = {
    "Technology": [("Apple", 180), ("Microsoft", 160), ("Google", 120), ("NVIDIA", 95), ("Meta", 75)],
    "Finance": [("JPMorgan", 85), ("Visa", 70), ("Mastercard", 55), ("Goldman Sachs", 45)],
    "Healthcare": [("UnitedHealth", 90), ("J&J", 65), ("Merck", 50), ("Pfizer", 40)],
    "Retail": [("Amazon", 140), ("Walmart", 60), ("Costco", 45), ("Target", 30)],
}

records = []
for sector, companies in sectors.items():
    for name, value in companies:
        records.append({"name": name, "value": value, "sector": sector, "radius": np.sqrt(value) * 4})

df = pd.DataFrame(records).sort_values("radius", ascending=False).reset_index(drop=True)

# Circle packing - place circles greedily closest to center without overlap
placed_x, placed_y, placed_r = [], [], []

for _, row in df.iterrows():
    r = row["radius"]

    if not placed_x:
        placed_x.append(0.0)
        placed_y.append(0.0)
        placed_r.append(r)
        continue

    best_pos, best_dist = None, float("inf")
    px_arr, py_arr, pr_arr = np.array(placed_x), np.array(placed_y), np.array(placed_r)

    for i in range(len(placed_x)):
        for angle in np.linspace(0, 2 * np.pi, 72, endpoint=False):
            gap = placed_r[i] + r + 2
            tx = placed_x[i] + gap * np.cos(angle)
            ty = placed_y[i] + gap * np.sin(angle)

            dists = np.sqrt((px_arr - tx) ** 2 + (py_arr - ty) ** 2)
            if np.all(dists >= pr_arr + r + 1):
                cdist = np.sqrt(tx**2 + ty**2)
                if cdist < best_dist:
                    best_dist = cdist
                    best_pos = (tx, ty)

    bx, by = best_pos if best_pos else (0.0, 0.0)
    placed_x.append(bx)
    placed_y.append(by)
    placed_r.append(r)

df["x"] = placed_x
df["y"] = placed_y

# Recenter coordinates into positive space
pad = 20
df["x"] = df["x"] - (df["x"] - df["radius"]).min() + pad
df["y"] = df["y"] - (df["y"] - df["radius"]).min() + pad
plot_w = (df["x"] + df["radius"]).max() + pad
plot_h = (df["y"] + df["radius"]).max() + pad

# Seaborn styling - distinctive context and style management
sns.set_context("poster", font_scale=0.85)
sns.set_style("white")

# Custom colorblind-safe palette anchored on Python Blue (#306998)
sector_order = list(sectors.keys())
base_colors = ["#306998", "#DE8F05", "#029E73", "#CC78BC"]
sector_palette = dict(zip(sector_order, sns.color_palette(base_colors), strict=True))

# Square canvas for better packing utilization (bubbles pack roughly circular)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_xlim(0, plot_w)
ax.set_ylim(0, plot_h)
ax.set_aspect("equal")

# Convert data-unit radii to scatter marker sizes (points²)
fig.canvas.draw()
px_per_unit = ax.transData.transform((1, 0))[0] - ax.transData.transform((0, 0))[0]
pts_per_unit = px_per_unit * 72 / fig.dpi
df["marker_size"] = (df["radius"] * 2 * pts_per_unit) ** 2

# Categorical ordering for consistent palette mapping
df["sector"] = pd.Categorical(df["sector"], categories=sector_order, ordered=True)

# Draw bubbles with seaborn scatterplot and hue mapping
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    hue="sector",
    size="marker_size",
    sizes=(df["marker_size"].min(), df["marker_size"].max()),
    hue_order=sector_order,
    palette=sector_palette,
    alpha=0.92,
    edgecolor="white",
    linewidth=3,
    legend="brief",
    ax=ax,
)

# Filter legend to sector entries only, then reposition with sns.move_legend
handles, labels = ax.get_legend_handles_labels()
sector_h = [h for h, lab in zip(handles, labels, strict=False) if lab in sector_order]
sector_lab = [lab for lab in labels if lab in sector_order]
ax.legend(sector_h, sector_lab)
sns.move_legend(
    ax,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.02),
    ncol=4,
    fontsize=16,
    framealpha=0.95,
    title="Sector",
    title_fontsize=18,
    edgecolor="#CCCCCC",
)

# Labels with value annotations for data storytelling
for _, row in df.iterrows():
    r = row["radius"]
    name = row["name"]
    value = row["value"]

    if r > 38:
        fs_name, max_chars, show_val = 20, 12, True
    elif r > 30:
        fs_name, max_chars, show_val = 16, 12, True
    elif r > 24:
        fs_name, max_chars, show_val = 12, 10, True
    else:
        fs_name, max_chars, show_val = 9, 8, False

    if len(name) > max_chars:
        name = name[: max_chars - 1] + "."

    if show_val:
        y_off = r * 0.13
        ax.text(
            row["x"],
            row["y"] + y_off,
            name,
            ha="center",
            va="center",
            fontsize=fs_name,
            fontweight="bold",
            color="white",
        )
        ax.text(
            row["x"],
            row["y"] - y_off * 2,
            f"${value}B",
            ha="center",
            va="center",
            fontsize=fs_name - 4,
            color="white",
            alpha=0.8,
        )
    else:
        ax.text(row["x"], row["y"], name, ha="center", va="center", fontsize=fs_name, fontweight="bold", color="white")

ax.axis("off")

# Title
ax.set_title(
    "Market Capitalization by Sector\nbubble-packed \u00b7 seaborn \u00b7 pyplots.ai",
    fontsize=26,
    fontweight="medium",
    pad=25,
    linespacing=1.4,
)

sns.despine(left=True, bottom=True)
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
