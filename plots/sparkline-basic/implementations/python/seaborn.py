""" anyplot.ai
sparkline-basic: Basic Sparkline
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme-adaptive chrome (Imprint palette) ---------------------------------
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series is ALWAYS brand green
BRAND = "#009E73"  # brand green — the sparkline line
LOW = "#AE3030"  # matte red — semantic anchor for the low point

# Data — daily readings for six dashboard KPIs ----------------------------
rng = np.random.default_rng(42)
metrics = [
    ("Revenue", "$", "K", 124.0, 0.9),
    ("Active Users", "", "K", 48.0, 0.7),
    ("Conversion", "", "%", 3.4, 0.04),
    ("Avg Session", "", "s", 182.0, 2.2),
    ("Churn", "", "%", 2.3, 0.05),
    ("NPS", "", "", 54.0, 0.8),
]
N_DAYS = 40
series = {}
for name, _prefix, _suffix, base, vol in metrics:
    walk = np.cumsum(rng.normal(0, vol, N_DAYS))
    series[name] = base + walk - walk[0]

# Theme — strip every default chrome element; sparklines carry none --------
sns.set_theme(
    style="white",
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK, "font.family": "sans-serif"},
)

fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(8, 4.5), dpi=400, constrained_layout=True)
fig.set_constrained_layout_pads(w_pad=0.18, h_pad=0.20, hspace=0.06, wspace=0.10)

x = np.arange(N_DAYS)

for ax, (name, prefix, suffix, _base, _vol) in zip(axes.ravel(), metrics, strict=True):
    y = series[name]

    # Sparkline line (seaborn) + subtle area fill
    sns.lineplot(x=x, y=y, ax=ax, color=BRAND, linewidth=2.2)
    ax.fill_between(x, y.min(), y, color=BRAND, alpha=0.12, linewidth=0)

    # Highlight min (red), max (brand green), and the current value
    i_min, i_max = int(np.argmin(y)), int(np.argmax(y))
    ax.scatter(i_min, y[i_min], color=LOW, s=42, zorder=5, edgecolors=PAGE_BG, linewidths=1.2)
    ax.scatter(i_max, y[i_max], color=BRAND, s=42, zorder=5, edgecolors=PAGE_BG, linewidths=1.2)
    ax.scatter(x[-1], y[-1], color=BRAND, s=60, zorder=6, edgecolors=PAGE_BG, linewidths=1.4)

    # Breathing room above/below the trace
    span = y.max() - y.min()
    ax.set_ylim(y.min() - span * 0.35, y.max() + span * 0.45)
    ax.set_xlim(-1, N_DAYS + 7)

    # Metric label (top-left) — the only text chrome a sparkline keeps
    ax.set_title(name, loc="left", fontsize=9, fontweight="bold", color=INK, pad=4)

    # Current value + trend delta vs. start (arrow makes direction explicit)
    last = y[-1]
    delta = (last - y[0]) / y[0] * 100
    arrow, dcolor = ("▲", BRAND) if delta >= 0 else ("▼", LOW)
    ax.text(
        0.99,
        0.93,
        f"{prefix}{last:,.1f}{suffix}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.99,
        0.62,
        f"{arrow} {abs(delta):.1f}%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        color=dcolor,
    )

    # Pure sparkline: remove all axes chrome
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_visible(False)

fig.suptitle("sparkline-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
