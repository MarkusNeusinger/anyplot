"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-23
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

# Circle packing - place circles one by one, closest to center without overlap
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

# Recenter so all coordinates are positive
pad = 20
df["x"] = df["x"] - (df["x"] - df["radius"]).min() + pad
df["y"] = df["y"] - (df["y"] - df["radius"]).min() + pad
plot_w = (df["x"] + df["radius"]).max() + pad
plot_h = (df["y"] + df["radius"]).max() + pad

# Seaborn styling
sns.set_theme(style="white", context="talk", font_scale=1.2)
palette = sns.color_palette("Set2", n_colors=len(sectors))
sector_colors = dict(zip(sectors.keys(), palette, strict=True))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(0, plot_w)
ax.set_ylim(0, plot_h)
ax.set_aspect("equal")

# Compute scatter marker sizes: convert data-unit diameter to points^2
# At dpi=100 (default), figsize=(16,9) => 1600x900 pixels for the figure
# With aspect="equal", the effective data range that fits is limited by the smaller axis
fig.canvas.draw()
transform = ax.transData
# Get scale: how many display points per data unit
p0 = transform.transform((0, 0))
p1 = transform.transform((1, 0))
pts_per_unit = (p1[0] - p0[0]) * 72 / fig.dpi  # convert pixels to points
df["marker_size"] = (df["radius"] * 2 * pts_per_unit) ** 2

# Draw bubbles with seaborn scatterplot
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    hue="sector",
    size="marker_size",
    sizes=(df["marker_size"].min(), df["marker_size"].max()),
    palette=sector_colors,
    alpha=0.9,
    edgecolor="white",
    linewidth=3,
    legend=False,
    ax=ax,
)

# Labels inside circles - scale font with bubble size, clip long names
for _, row in df.iterrows():
    label = row["name"]
    r = row["radius"]
    if r > 38:
        fs, max_chars = 18, 12
    elif r > 30:
        fs, max_chars = 14, 12
    elif r > 24:
        fs, max_chars = 11, 10
    else:
        fs, max_chars = 8, 7
    if len(label) > max_chars:
        label = label[: max_chars - 1] + "."
    ax.text(row["x"], row["y"], label, ha="center", va="center", fontsize=fs, fontweight="bold", color="white")

ax.axis("off")

# Title
ax.set_title(
    "Market Capitalization by Sector\nbubble-packed \u00b7 seaborn \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=20,
    linespacing=1.4,
)

# Legend with circular markers matching bubble colors
handles = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=sector_colors[s], markersize=14, label=s)
    for s in sectors
]
ax.legend(
    handles=handles,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.01),
    ncol=4,
    fontsize=14,
    framealpha=0.95,
    title="Sector",
    title_fontsize=16,
    edgecolor="gray",
)

sns.despine(left=True, bottom=True)
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
