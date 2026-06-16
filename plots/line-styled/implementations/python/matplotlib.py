""" anyplot.ai
line-styled: Styled Line Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - CPU performance benchmarks over time
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Simulated performance scores for different processors
base_score = 100
processor_a = base_score + np.cumsum(np.random.randn(12) * 3 + 2)
processor_b = base_score + np.cumsum(np.random.randn(12) * 4 + 1.5)
processor_c = base_score + np.cumsum(np.random.randn(12) * 2 + 2.5)
processor_d = base_score + np.cumsum(np.random.randn(12) * 3 + 0.5)

series_data = [processor_a, processor_b, processor_c, processor_d]
series_names = ["Series 1", "Series 2", "Series 3", "Series 4"]
line_styles = ["-", "--", ":", "-."]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot lines with different styles
for i, (data, name, style) in enumerate(
    zip(series_data, series_names, line_styles, strict=True)
):
    ax.plot(months, data, linestyle=style, linewidth=3, color=COLORS[i], label=name)

# Style
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Performance Score", fontsize=20, color=INK)
ax.set_title("line-styled · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(PAGE_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
