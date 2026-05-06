""" anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Created: 2026-05-06
"""

import os
import sys


# Avoid shadowing of seaborn/matplotlib packages by this file's name
script_dir = os.path.dirname(os.path.abspath(__file__))
sys_path_saved = sys.path.copy()
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


sys.path = sys_path_saved

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND_GREEN = "#009E73"
ACCENT_RED = "#D55E00"
ACCENT_BLUE = "#0072B2"

# Data: Quarterly financial breakdown
categories = ["Starting Balance", "Sales", "Returns", "COGS", "Operating Costs", "Taxes", "Net Profit"]
values = [100000, 150000, -25000, -60000, -30000, -18000, 117000]

# Create DataFrame with calculated positions for waterfall
data = []
cumulative = 0
for i, (cat, val) in enumerate(zip(categories, values, strict=True)):
    if i == 0:
        # Starting bar
        start = 0
        end = val
        cumulative = val
        color = ACCENT_BLUE
        is_total = True
    elif i == len(categories) - 1:
        # Final total bar
        start = 0
        end = cumulative
        color = ACCENT_BLUE
        is_total = True
    else:
        # Intermediate bars
        start = cumulative
        end = cumulative + val
        cumulative = end
        color = BRAND_GREEN if val > 0 else ACCENT_RED
        is_total = False

    data.append(
        {
            "category": cat,
            "value": val,
            "start": start,
            "end": end,
            "height": abs(val) if i != 0 and i != len(categories) - 1 else abs(end),
            "color": color,
            "is_total": is_total,
            "index": i,
        }
    )

df = pd.DataFrame(data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Configure seaborn theme
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
        "grid.alpha": 0.10,
    },
)

# Plot waterfall bars
bar_width = 0.6
for idx, row in df.iterrows():
    if row["is_total"]:
        # Total bars span from 0
        ax.bar(
            row["index"],
            row["end"],
            bar_width,
            bottom=0,
            color=row["color"],
            edgecolor=PAGE_BG,
            linewidth=1.5,
            alpha=0.85,
        )
    else:
        # Intermediate bars start from previous cumulative
        ax.bar(
            row["index"],
            row["height"],
            bar_width,
            bottom=row["start"],
            color=row["color"],
            edgecolor=PAGE_BG,
            linewidth=1.5,
            alpha=0.85,
        )

    # Add connecting line to next bar (except for last bar)
    if idx < len(df) - 1:
        next_row = df.iloc[idx + 1]
        if row["is_total"]:
            line_y = row["end"]
        else:
            line_y = row["end"]

        if not next_row["is_total"]:
            ax.plot(
                [row["index"] + bar_width / 2, next_row["index"] - bar_width / 2],
                [line_y, line_y],
                color=INK_SOFT,
                linewidth=1.5,
                linestyle="--",
                alpha=0.6,
            )

    # Add value labels on bars
    if row["is_total"]:
        label_y = row["end"] / 2
        label_value = f"${row['end']:,.0f}"
    else:
        label_y = row["start"] + row["height"] / 2
        label_value = f"${row['value']:,.0f}"

    ax.text(row["index"], label_y, label_value, ha="center", va="center", fontsize=14, color=INK, fontweight="medium")

# Style
ax.set_xticks(range(len(df)))
ax.set_xticklabels(df["category"], fontsize=16)
ax.set_ylabel("Amount ($)", fontsize=20, color=INK)
ax.set_title(
    "Quarterly Financial Breakdown · waterfall-basic · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=20,
)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x / 1000:.0f}K"))

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
