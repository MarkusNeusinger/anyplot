""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Semantic direction colors — imprint diverging anchors
COLOR_POS = "#AE3030"  # red: positive SHAP (pushes prediction up)
COLOR_NEG = "#4467A3"  # blue: negative SHAP (pushes prediction down)

# Data — credit loan approval model, individual applicant explanation
# Features ordered by absolute SHAP magnitude, largest first (top of chart)
features_desc = [
    "Monthly Income",
    "Debt-to-Income Ratio",
    "Credit Score",
    "Employment Duration",
    "Prior Defaults",
    "Loan Amount",
    "Age",
    "Open Credit Lines",
    "Savings Balance",
    "Recent Inquiries",
]
shap_desc = [0.24, -0.18, 0.15, 0.12, -0.10, -0.08, 0.06, 0.04, 0.03, -0.02]
base_value = 0.42  # E[f(x)]: mean approval probability across training set
final_value = base_value + sum(shap_desc)  # f(x) = 0.68

# Reverse for matplotlib bottom-to-top axis (largest magnitude at top)
features = features_desc[::-1]
shap_values = shap_desc[::-1]
n = len(features)
y_pos = np.arange(n)

# Compute bar left edges and cumulative running totals (bottom-to-top)
running = base_value
bar_lefts = []
cum_after = []
for sv in shap_values:
    bar_lefts.append(running + sv if sv < 0 else running)
    running += sv
    cum_after.append(running)

bar_widths = [abs(sv) for sv in shap_values]
bar_colors = [COLOR_POS if sv >= 0 else COLOR_NEG for sv in shap_values]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_axisbelow(True)

ax.barh(y_pos, bar_widths, left=bar_lefts, color=bar_colors, height=0.55, edgecolor=PAGE_BG, linewidth=1.5, zorder=3)

# Vertical connector lines in the gaps between bars at cumulative position
for i in range(n - 1):
    ax.plot(
        [cum_after[i], cum_after[i]],
        [y_pos[i] + 0.32, y_pos[i + 1] - 0.32],
        color=INK_MUTED,
        linewidth=1.2,
        linestyle="dotted",
        alpha=0.7,
        zorder=2,
    )

# Reference lines for base value and final prediction
ax.axvline(base_value, color=INK_MUTED, linewidth=1.5, linestyle="--", alpha=0.6)
ax.axvline(final_value, color=INK_SOFT, linewidth=2.0, linestyle="--", alpha=0.7)

# SHAP value text labels on (wide bars) or beside (narrow bars) each segment
LABEL_THRESH = 0.07
for i, (sv, left, width) in enumerate(zip(shap_values, bar_lefts, bar_widths, strict=False)):
    txt = f"+{sv:.2f}" if sv > 0 else f"{sv:.2f}"
    if width >= LABEL_THRESH:
        ax.text(
            left + width / 2,
            y_pos[i],
            txt,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color="white",
            zorder=5,
        )
    else:
        gap = 0.007
        if sv > 0:
            ax.text(
                left + width + gap,
                y_pos[i],
                txt,
                ha="left",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=COLOR_POS,
                zorder=5,
            )
        else:
            ax.text(
                left - gap,
                y_pos[i],
                txt,
                ha="right",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=COLOR_NEG,
                zorder=5,
            )

# Annotations for base value and final prediction above the top bar
top_y = n + 0.08
ax.text(
    base_value,
    top_y,
    f"E[f(x)] = {base_value:.2f}",
    ha="center",
    va="bottom",
    fontsize=13,
    color=INK_MUTED,
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_MUTED, "boxstyle": "round,pad=0.35", "alpha": 0.9},
)
ax.text(
    final_value,
    top_y,
    f"f(x) = {final_value:.2f}",
    ha="center",
    va="bottom",
    fontsize=13,
    fontweight="bold",
    color=INK,
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "boxstyle": "round,pad=0.35", "alpha": 0.9},
)

# Style
ax.set_yticks(y_pos)
ax.set_yticklabels(features, fontsize=16)
ax.set_xlabel("Loan Approval Probability", fontsize=20, color=INK)
ax.set_title("Credit Approval · shap-waterfall · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

all_x = bar_lefts + [b + w for b, w in zip(bar_lefts, bar_widths, strict=False)] + [base_value, final_value]
ax.set_xlim(min(all_x) - 0.06, max(all_x) + 0.09)
ax.set_ylim(-0.6, n + 0.9)

ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT, length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

ax.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend
pos_patch = mpatches.Patch(color=COLOR_POS, label="Positive contribution")
neg_patch = mpatches.Patch(color=COLOR_NEG, label="Negative contribution")
leg = ax.legend(handles=[pos_patch, neg_patch], fontsize=16, loc="lower right", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
