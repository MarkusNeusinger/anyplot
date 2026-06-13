""" anyplot.ai
curve-power-duration: Mean-Maximal Power Duration Curve
Library: matplotlib 3.11.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-06-13
"""

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# Theme tokens — Imprint palette chrome mapping
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Imprint position 1 — empirical MMP (always first series)
MODEL_CLR = "#4467A3"  # Imprint position 3 — CP model (semantic: blue = theoretical fit)

# Data — synthetic well-trained cyclist: CP = 280 W, W' = 20 kJ
np.random.seed(42)
CP = 280  # W — critical power aerobic asymptote
W_PRIME = 20000  # J — anaerobic work capacity
P_MAX = 1100  # W — neuromuscular peak power (1-s sprint)

# 60 log-spaced durations: 1 s → 18 000 s (5 h)
durations = np.logspace(0, np.log10(18000), 60)

# Empirical mean-maximal power: bounded by neuromuscular ceiling, monotonically non-increasing
raw = np.minimum(P_MAX, CP + W_PRIME / durations) + np.random.normal(3, 9, 60)
empirical = raw.copy()
for i in range(1, len(empirical)):
    empirical[i] = min(empirical[i], empirical[i - 1])

# Smooth CP model line (from 60 s — physiologically applicable range)
dur_model = np.logspace(np.log10(60), np.log10(18000), 400)
model_line = CP + W_PRIME / dur_model

# Plot canvas (3200 × 1800 px — no bbox_inches, figsize × dpi sets canvas exactly)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Primary series — empirical MMP (Imprint brand green, solid)
ax.plot(durations, empirical, color=BRAND, linewidth=2.8, label="Mean-Maximal Power", zorder=3)

# CP model fit (Imprint blue, dashed)
ax.plot(
    dur_model, model_line, color=MODEL_CLR, linewidth=2.0, linestyle="--", label="CP Model  (P = CP + W′/t)", zorder=2
)

# CP horizontal asymptote — annotated directly, not in legend
ax.axhline(y=CP, color=INK_MUTED, linewidth=1.3, linestyle=":", alpha=0.8, zorder=1)
ax.text(17000, CP + 12, f"CP = {CP} W", color=INK_MUTED, fontsize=7.5, ha="right", va="bottom")

# Reference duration vertical markers
ref_marks = {"5 s\nsprint": 5, "1 min": 60, "5 min": 300, "20 min\n(FTP)": 1200}
for label, dur in ref_marks.items():
    ax.axvline(x=dur, color=INK_SOFT, linewidth=0.8, linestyle=":", alpha=0.35, zorder=1)
    ax.text(dur, 1200, label, color=INK_SOFT, fontsize=7, ha="center", va="top", linespacing=1.25)

# X-axis — log scale with human-readable tick labels
ax.set_xscale("log")
tick_secs = [1, 5, 30, 60, 300, 1200, 3600, 10800, 18000]
tick_labels = ["1s", "5s", "30s", "1min", "5min", "20min", "1h", "3h", "5h"]
ax.set_xticks(tick_secs)
ax.set_xticklabels(tick_labels)
ax.xaxis.set_minor_locator(ticker.NullLocator())
ax.set_xlim(0.9, 20000)
ax.set_ylim(150, 1270)

# Style
title = "curve-power-duration · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel("Effort Duration", fontsize=10, color=INK, labelpad=6)
ax.set_ylabel("Power Output (W)", fontsize=10, color=INK, labelpad=6)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

# Legend — lower left has ample space (curve is above 1000 W there)
leg = ax.legend(fontsize=8, loc="lower left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.13)

# Save (bbox_inches omitted — figsize=(8,4.5) × dpi=400 → exactly 3200×1800)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
