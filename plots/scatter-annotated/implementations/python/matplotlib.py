"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses position 1 (brand green)
BRAND = "#009E73"

# Columns: set these to your table's column names
COMPANY = "Company"  # role: label
MARKET_CAP = "Market Capitalization ($ Billions)"  # role: x
REVENUE = "Annual Revenue ($ Billions)"  # role: y
LABEL_DX = "Label offset x (pt)"  # role: extra
LABEL_DY = "Label offset y (pt)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("companies.csv")
df = pd.DataFrame(
    {
        COMPANY: [
            "TechCorp",
            "DataSys",
            "CloudNet",
            "ByteWorks",
            "QuantumAI",
            "NexGen",
            "CyberFlow",
            "InfoPrime",
            "CodeLabs",
            "DigiCore",
            "NetSphere",
            "AlgoTech",
            "VisionX",
            "PulseTech",
            "ZetaLogic",
        ],
        MARKET_CAP: [55, 135, 105, 18, 225, 70, 120, 45, 165, 85, 30, 195, 150, 175, 60],
        REVENUE: [12, 42, 30, 4, 65, 18, 38, 10, 52, 24, 6, 58, 45, 50, 15],
        LABEL_DX: [5, -5, 5, 5, 5, 5, 5, 5, -6, 5, -5, 5, 5, 5, -5],
        LABEL_DY: [-5, 4, 4, -6, 4, 5, -5, -5, 4, 4, 7, -6, 4, 5, 5],
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(df[MARKET_CAP], df[REVENUE], s=70, alpha=0.7, color=BRAND, edgecolors=PAGE_BG, linewidths=1, zorder=3)

# Labels sit beside their points; thin leader lines tie each one back to its marker
for _, row in df.iterrows():
    ax.annotate(
        row[COMPANY],
        xy=(row[MARKET_CAP], row[REVENUE]),
        xytext=(row[LABEL_DX], row[LABEL_DY]),
        textcoords="offset points",
        fontsize=8,
        color=INK,
        fontweight="medium",
        ha="left" if row[LABEL_DX] > 0 else "right",
        va="center",
        arrowprops={"arrowstyle": "-", "color": INK_SOFT, "lw": 0.6, "shrinkA": 0, "shrinkB": 2},
        zorder=4,
    )

# Style
ax.set_xlabel(MARKET_CAP, fontsize=10, color=INK)
ax.set_ylabel(REVENUE, fontsize=10, color=INK)
ax.set_title("scatter-annotated · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

ax.set_xlim(0, df[MARKET_CAP].max() * 1.13)
ax.set_ylim(0, df[REVENUE].max() * 1.08)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
