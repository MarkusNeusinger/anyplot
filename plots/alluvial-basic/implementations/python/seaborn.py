""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series always #009E73
IMPRINT = [
    "#009E73",  # 1. bluish green (brand)
    "#C475FD",  # 2. vermillion
    "#4467A3",  # 3. blue
    "#BD8233",  # 4. reddish purple
]

# Data: Employment sector transitions across 4 years
np.random.seed(42)

years = ["2021", "2022", "2023", "2024"]
sectors = ["Technology", "Finance", "Healthcare", "Manufacturing"]

# Employment counts (thousands) at each time point
sector_counts = np.array(
    [
        [450, 520, 580, 620],  # Technology
        [280, 290, 310, 315],  # Finance
        [320, 340, 360, 380],  # Healthcare
        [250, 230, 210, 190],  # Manufacturing
    ]
)

# Flow transitions between consecutive years
flows = [
    # 2021 -> 2022
    {
        ("Technology", "Technology"): 400,
        ("Technology", "Finance"): 25,
        ("Technology", "Healthcare"): 15,
        ("Technology", "Manufacturing"): 10,
        ("Finance", "Technology"): 20,
        ("Finance", "Finance"): 250,
        ("Finance", "Healthcare"): 5,
        ("Finance", "Manufacturing"): 5,
        ("Healthcare", "Technology"): 10,
        ("Healthcare", "Finance"): 5,
        ("Healthcare", "Healthcare"): 300,
        ("Healthcare", "Manufacturing"): 5,
        ("Manufacturing", "Technology"): 70,
        ("Manufacturing", "Finance"): 10,
        ("Manufacturing", "Healthcare"): 40,
        ("Manufacturing", "Manufacturing"): 130,
    },
    # 2022 -> 2023
    {
        ("Technology", "Technology"): 480,
        ("Technology", "Finance"): 15,
        ("Technology", "Healthcare"): 20,
        ("Technology", "Manufacturing"): 5,
        ("Finance", "Technology"): 35,
        ("Finance", "Finance"): 245,
        ("Finance", "Healthcare"): 5,
        ("Finance", "Manufacturing"): 5,
        ("Healthcare", "Technology"): 30,
        ("Healthcare", "Finance"): 10,
        ("Healthcare", "Healthcare"): 295,
        ("Healthcare", "Manufacturing"): 5,
        ("Manufacturing", "Technology"): 50,
        ("Manufacturing", "Finance"): 5,
        ("Manufacturing", "Healthcare"): 25,
        ("Manufacturing", "Manufacturing"): 150,
    },
    # 2023 -> 2024
    {
        ("Technology", "Technology"): 550,
        ("Technology", "Finance"): 10,
        ("Technology", "Healthcare"): 15,
        ("Technology", "Manufacturing"): 5,
        ("Finance", "Technology"): 30,
        ("Finance", "Finance"): 280,
        ("Finance", "Healthcare"): 3,
        ("Finance", "Manufacturing"): 2,
        ("Healthcare", "Technology"): 50,
        ("Healthcare", "Finance"): 8,
        ("Healthcare", "Healthcare"): 295,
        ("Healthcare", "Manufacturing"): 7,
        ("Manufacturing", "Technology"): 25,
        ("Manufacturing", "Finance"): 3,
        ("Manufacturing", "Healthcare"): 30,
        ("Manufacturing", "Manufacturing"): 152,
    },
]

# Create mapping from sector to color
sector_colors = {sector: IMPRINT[i] for i, sector in enumerate(sectors)}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Calculate positions for each time point
n_years = len(years)
x_positions = np.linspace(0, 10, n_years)
bar_width = 0.6
total_height = 100

# Track positions for each node
node_positions = {}

# Draw nodes (stacked bars) at each time point
for year_idx, year in enumerate(years):
    x = x_positions[year_idx]
    year_total = sector_counts[:, year_idx].sum()

    y_bottom = 0
    for sector_idx, sector in enumerate(sectors):
        height = (sector_counts[sector_idx, year_idx] / year_total) * total_height
        y_top = y_bottom + height

        node_positions[(year_idx, sector)] = (y_bottom, y_top)

        # Draw the bar segment
        rect = mpatches.Rectangle(
            (x - bar_width / 2, y_bottom),
            bar_width,
            height,
            facecolor=sector_colors[sector],
            edgecolor=PAGE_BG,
            linewidth=1.5,
        )
        ax.add_patch(rect)

        # Add sector labels on first and last columns
        count = sector_counts[sector_idx, year_idx]
        label_text = f"{sector} ({count}k)"
        font_size = 14

        if year_idx == 0:
            ax.text(
                x - bar_width / 2 - 0.2,
                (y_bottom + y_top) / 2,
                label_text,
                ha="right",
                va="center",
                fontsize=font_size,
                fontweight="bold",
                color=sector_colors[sector],
            )
        elif year_idx == n_years - 1:
            ax.text(
                x + bar_width / 2 + 0.2,
                (y_bottom + y_top) / 2,
                label_text,
                ha="left",
                va="center",
                fontsize=font_size,
                fontweight="bold",
                color=sector_colors[sector],
            )

        y_bottom = y_top

    # Add year labels
    year_total_display = sector_counts[:, year_idx].sum()
    ax.text(
        x,
        total_height + 3,
        f"{year}\n({year_total_display}k total)",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )

# Draw flows between consecutive time points
for flow_idx, flow_dict in enumerate(flows):
    x0 = x_positions[flow_idx]
    x1 = x_positions[flow_idx + 1]

    year0_total = sector_counts[:, flow_idx].sum()
    year1_total = sector_counts[:, flow_idx + 1].sum()

    source_offsets = {sector: node_positions[(flow_idx, sector)][0] for sector in sectors}
    target_offsets = {sector: node_positions[(flow_idx + 1, sector)][0] for sector in sectors}

    for (source_sector, target_sector), flow_value in flow_dict.items():
        if flow_value <= 0:
            continue

        source_height = (flow_value / year0_total) * total_height
        target_height = (flow_value / year1_total) * total_height

        y0_bot = source_offsets[source_sector]
        y0_top = y0_bot + source_height
        y1_bot = target_offsets[target_sector]
        y1_top = y1_bot + target_height

        # Draw curved band
        band_x0 = x0 + bar_width / 2
        band_x1 = x1 - bar_width / 2
        cx0 = band_x0 + 0.4 * (band_x1 - band_x0)
        cx1 = band_x0 + 0.6 * (band_x1 - band_x0)

        verts = [
            (band_x0, y0_bot),
            (cx0, y0_bot),
            (cx1, y1_bot),
            (band_x1, y1_bot),
            (band_x1, y1_top),
            (cx1, y1_top),
            (cx0, y0_top),
            (band_x0, y0_top),
            (band_x0, y0_bot),
        ]
        codes = [
            mpatches.Path.MOVETO,
            mpatches.Path.CURVE4,
            mpatches.Path.CURVE4,
            mpatches.Path.CURVE4,
            mpatches.Path.LINETO,
            mpatches.Path.CURVE4,
            mpatches.Path.CURVE4,
            mpatches.Path.CURVE4,
            mpatches.Path.CLOSEPOLY,
        ]
        path = mpatches.Path(verts, codes)
        min_height = min(source_height, target_height)
        alpha = 0.5 if min_height < 3 else 0.35
        patch = mpatches.PathPatch(
            path,
            facecolor=sector_colors[source_sector],
            edgecolor=sector_colors[source_sector],
            linewidth=0.5,
            alpha=alpha,
        )
        ax.add_patch(patch)

        source_offsets[source_sector] = y0_top
        target_offsets[target_sector] = y1_top

# Add legend
legend_patches = [
    mpatches.Patch(facecolor=sector_colors[sector], edgecolor=PAGE_BG, label=sector) for sector in sectors
]
ax.legend(
    handles=legend_patches,
    loc="upper right",
    fontsize=14,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    framealpha=0.95,
)

# Styling
ax.set_xlim(-2.8, 13.3)
ax.set_ylim(-8, 120)
ax.set_aspect("auto")

ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

# Title
ax.set_title("alluvial-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=25)

# Subtitle with data context
ax.text(
    5,
    -5,
    "Employment Sector Transitions 2021-2024 | Values in thousands | Flow width proportional to transitions",
    ha="center",
    va="top",
    fontsize=14,
    color=INK_SOFT,
    style="italic",
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
