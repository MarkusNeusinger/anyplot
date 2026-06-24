""" anyplot.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 92/100 | Updated: 2026-06-24
"""

import os
import sys


# Remove the script's own directory from sys.path so sibling files (e.g. matplotlib.py)
# do not shadow installed packages when running from the implementations directory.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]
del _here

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns
from scipy import stats


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73 (brand green)
BRAND = "#009E73"

# Data — enzyme-catalyzed hydrolysis (alkaline phosphatase) across physiological temperatures
# Domain: enzyme kinetics, Ea ~58 kJ/mol (lower than thermal decomposition, typical for enzymes)
temperature_K = np.array([278, 283, 288, 293, 298, 303, 308, 313, 320, 330])
R = 8.314  # gas constant (J/mol·K)
Ea_true = 58000  # activation energy (J/mol)
A = 1.2e9  # pre-exponential factor (s⁻¹)

np.random.seed(7)
noise = np.random.normal(0, 0.28, len(temperature_K))
rate_constant_k = A * np.exp(-Ea_true / (R * temperature_K)) * np.exp(noise)
rate_constant_k[7] *= 2.0  # one elevated outlier at 313 K — demonstrates regression robustness

inv_T = 1.0 / temperature_K
ln_k = np.log(rate_constant_k)

# Linear regression for annotation
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_extracted = -slope * R

# Seaborn theme setup with full theme-adaptive chrome
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
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
    },
)

# Canvas: landscape 3200×1800 — figsize=(8, 4.5) × dpi=400
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.patch.set_facecolor(PAGE_BG)

# Main plot — sns.regplot with 95% CI band is idiomatic seaborn for regression + scatter
sns.regplot(
    x=inv_T,
    y=ln_k,
    ci=95,
    scatter_kws={"s": 170, "color": BRAND, "edgecolor": "white", "linewidths": 1.5, "zorder": 5},
    line_kws={"color": BRAND, "linewidth": 2.5, "alpha": 0.9},
    ax=ax,
)

# Fix CI band visibility in dark theme — regplot draws the band as a PolyCollection
# with low default alpha; raise it in dark mode so it reads against #1A1A17
for coll in ax.collections:
    coll.set_facecolor(BRAND)
    coll.set_alpha(0.38 if THEME == "dark" else 0.18)

# Outlier annotation — raised to 8pt (above mobile-readable minimum)
ax.annotate(
    "outlier",
    xy=(inv_T[7], ln_k[7]),
    xytext=(6, 10),
    textcoords="offset points",
    fontsize=8,
    color=INK_MUTED,
    arrowprops={"arrowstyle": "-", "color": INK_MUTED, "lw": 0.8},
)

# Annotation box with extracted kinetic parameters
annotation_text = f"$R^2$ = {r_squared:.4f}\nSlope = {slope:.0f} K\n$E_a$ = {Ea_extracted / 1000:.1f} kJ/mol"
ax.text(
    0.03,
    0.38,
    annotation_text,
    transform=ax.transAxes,
    fontsize=8,
    verticalalignment="top",
    horizontalalignment="left",
    color=INK,
    bbox={"boxstyle": "round,pad=0.6", "facecolor": ELEVATED_BG, "edgecolor": BRAND, "alpha": 0.95, "linewidth": 1.5},
)

# Secondary x-axis — temperature in Kelvin for chemical context
ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
temp_ticks_K = np.array([278, 293, 303, 313, 330])
ax_top.set_xticks(1.0 / temp_ticks_K)
ax_top.set_xticklabels([f"{t} K" for t in temp_ticks_K], fontsize=8)
ax_top.set_xlabel("Temperature (K)", fontsize=9, labelpad=8, color=INK)
# Tick-less secondary axis: labels only, no tick marks — cleaner composition
ax_top.tick_params(axis="x", labelsize=8, colors=INK_SOFT, length=0)
ax_top.spines["top"].set_color(INK_SOFT)
ax_top.spines["right"].set_visible(False)

# Bottom axis styling
ax.set_xlabel("1/T (K⁻¹)", fontsize=10, color=INK)
ax.set_ylabel("ln(k)", fontsize=10, color=INK)
ax.set_title("line-arrhenius · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.grid(True, alpha=0.08, linewidth=0.6, color=INK)
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.4f"))

# Explicit spine cleanup (belt-and-suspenders alongside rc — seaborn despine idiom)
sns.despine(ax=ax, top=True, right=True)

fig.subplots_adjust(top=0.78, bottom=0.15, left=0.10, right=0.97)
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"plot-{THEME}.png")
plt.savefig(_out, dpi=400, facecolor=PAGE_BG)
plt.close(fig)
