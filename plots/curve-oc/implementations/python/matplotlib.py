""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-19
"""

from math import comb

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data
fraction_defective = np.linspace(0, 0.15, 200)

sampling_plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1"},
    {"n": 80, "c": 2, "label": "n=80, c=2"},
    {"n": 100, "c": 2, "label": "n=100, c=2"},
]

oc_curves = {}
for plan in sampling_plans:
    n, c = plan["n"], plan["c"]
    prob_accept = sum(comb(n, k) * fraction_defective**k * (1 - fraction_defective) ** (n - k) for k in range(c + 1))
    oc_curves[plan["label"]] = prob_accept

aql = 0.02
ltpd = 0.10

# Plot
colors = ["#306998", "#D4A03C", "#8B4F6E"]
fig, ax = plt.subplots(figsize=(16, 9))

for (label, prob_accept), color in zip(oc_curves.items(), colors, strict=False):
    ax.plot(fraction_defective, prob_accept, linewidth=3, color=color, label=label)

# Shaded risk regions using fill_between
n0, c0 = sampling_plans[0]["n"], sampling_plans[0]["c"]
first_curve = oc_curves[sampling_plans[0]["label"]]

# Producer's risk region (alpha): shade between curve and 1.0 at AQL
aql_mask = fraction_defective <= aql
ax.fill_between(
    fraction_defective[aql_mask], first_curve[aql_mask], 1.0, alpha=0.12, color=colors[0], label="Producer's risk (α)"
)

# Consumer's risk region (beta): shade between 0 and curve at LTPD
ltpd_mask = fraction_defective >= ltpd
ax.fill_between(
    fraction_defective[ltpd_mask], 0, first_curve[ltpd_mask], alpha=0.12, color="#C04040", label="Consumer's risk (β)"
)

# AQL and LTPD reference lines
ax.axvline(x=aql, color="#888888", linestyle="--", linewidth=1.5, alpha=0.6)
ax.axvline(x=ltpd, color="#888888", linestyle="--", linewidth=1.5, alpha=0.6)

ax.text(aql + 0.002, 0.96, "AQL", fontsize=14, fontweight="bold", color="#555555", ha="left", va="top")
ax.text(ltpd + 0.002, 0.96, "LTPD", fontsize=14, fontweight="bold", color="#555555", ha="left", va="top")

# Producer's risk (alpha) annotation at AQL for first plan
pa_at_aql = sum(comb(n0, k) * aql**k * (1 - aql) ** (n0 - k) for k in range(c0 + 1))
alpha_value = 1 - pa_at_aql
ax.plot(aql, pa_at_aql, "o", color=colors[0], markersize=10, zorder=5)
ax.annotate(
    f"α = {alpha_value:.2f}",
    xy=(aql, pa_at_aql),
    xytext=(aql + 0.015, pa_at_aql - 0.06),
    fontsize=14,
    color=colors[0],
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": colors[0], "lw": 1.5},
)

# Consumer's risk (beta) annotation at LTPD for first plan
beta_value = sum(comb(n0, k) * ltpd**k * (1 - ltpd) ** (n0 - k) for k in range(c0 + 1))
ax.plot(ltpd, beta_value, "o", color="#C04040", markersize=10, zorder=5)
ax.annotate(
    f"β = {beta_value:.2f}",
    xy=(ltpd, beta_value),
    xytext=(ltpd + 0.012, beta_value + 0.08),
    fontsize=14,
    color="#C04040",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#C04040", "lw": 1.5},
)

# Axis formatting using FuncFormatter for percentage display
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0%}"))
ax.xaxis.set_major_locator(mticker.MultipleLocator(0.02))

# Style
ax.set_xlabel("Fraction Defective (p)", fontsize=20)
ax.set_ylabel("Probability of Acceptance P(accept)", fontsize=20)
ax.set_title("curve-oc · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=14, frameon=False, loc="upper right")
ax.set_xlim(0, 0.15)
ax.set_ylim(-0.02, 1.05)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
