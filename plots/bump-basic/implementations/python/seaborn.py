"""anyplot.ai
bump-basic: Basic Bump Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 8 hues, canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Theme-adaptive seaborn setup
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

# Columns: set these to your table's column names
COMPANY = "Company"  # role: entity
QUARTER = "Quarter"  # role: period
RANK = "Market cap rank"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("ranks.csv")
quarters = ["Q1'23", "Q2'23", "Q3'23", "Q4'23", "Q1'24", "Q2'24", "Q3'24", "Q4'24"]
ranks_data = {
    "Apple": [1, 1, 1, 1, 2, 1, 1, 1],
    "Microsoft": [2, 2, 2, 2, 1, 2, 3, 3],
    "Amazon": [4, 4, 4, 4, 4, 5, 5, 4],
    "Alphabet": [3, 3, 3, 3, 5, 4, 4, 5],
    "Nvidia": [5, 5, 5, 5, 3, 3, 2, 2],
}
df = pd.DataFrame(
    [
        {COMPANY: company, QUARTER: quarter, RANK: rank}
        for company, company_ranks in ranks_data.items()
        for quarter, rank in zip(quarters, company_ranks, strict=True)
    ]
)

# Plot: reads only df and the constants above
companies = list(df[COMPANY].unique())
n_companies = len(companies)
palette = IMPRINT_PALETTE[:n_companies]

# Figure-level relplot: hue + style give each company a color and a marker shape
g = sns.relplot(
    data=df,
    x=QUARTER,
    y=RANK,
    hue=COMPANY,
    style=COMPANY,
    markers=True,
    dashes=False,
    markersize=14,
    linewidth=3,
    palette=palette,
    hue_order=companies,
    sort=False,
    kind="line",
    height=4.5,
    aspect=16 / 9,
    legend=False,
)
g.figure.set_dpi(400)
g.figure.set_size_inches(8, 4.5)
ax = g.axes[0, 0]

# Rank 1 at the top, ticks at whole-number ranks only
ax.invert_yaxis()
ax.set_yticks(range(int(df[RANK].min()), int(df[RANK].max()) + 1))
ax.xaxis.grid(False)
ax.yaxis.grid(True)
sns.despine(ax=ax)

# End-of-line labels replace the legend
period_order = list(df[QUARTER].unique())
ends = df.dropna(subset=[RANK]).groupby(COMPANY, sort=False).tail(1).set_index(COMPANY)
for i, company in enumerate(companies):
    if company not in ends.index:
        continue
    ax.annotate(
        company,
        xy=(period_order.index(ends.loc[company, QUARTER]), ends.loc[company, RANK]),
        xytext=(18, 0),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        va="center",
    )

# Style
ax.set_title("bump-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel(QUARTER, fontsize=10, color=INK)
ax.set_ylabel(RANK, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

g.figure.canvas.draw()
g.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
