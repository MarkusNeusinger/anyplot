""" anyplot.ai
histogram-density: Density Histogram
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DELIVERY_TIME = "Delivery time (minutes)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("deliveries.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({DELIVERY_TIME: rng.lognormal(mean=3.4, sigma=0.45, size=600)})

# Plot: reads only df and the constants above
values = df[DELIVERY_TIME].dropna()
mean = values.mean()

# Log-normal density fitted to the sample, evaluated on the same density scale as the bars
log_values = np.log(values)
mu, sigma = log_values.mean(), log_values.std()
x_pdf = np.linspace(values.min() * 0.9, values.max() * 1.05, 400)
pdf = np.exp(-((np.log(x_pdf) - mu) ** 2) / (2 * sigma**2)) / (x_pdf * sigma * np.sqrt(2 * np.pi))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.hist(
    values,
    bins=30,
    density=True,
    alpha=0.8,
    color=IMPRINT_PALETTE[0],
    edgecolor=PAGE_BG,
    linewidth=0.6,
    label="Observed deliveries",
)
ax.plot(x_pdf, pdf, color=IMPRINT_PALETTE[1], linewidth=2.5, label=f"Log-normal fit (μ={mu:.2f}, σ={sigma:.2f})")
ax.axvline(mean, color=INK_SOFT, linestyle="--", linewidth=1.5, label=f"Mean = {mean:.1f} min")

# Style
ax.set_title("histogram-density · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DELIVERY_TIME, fontsize=10, color=INK)
ax.set_ylabel("Probability density (1/minute)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.set_xlim(0, x_pdf.max())
ax.set_ylim(0, None)

leg = ax.legend(fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.5)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
