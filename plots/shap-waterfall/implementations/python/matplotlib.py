""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-12
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (full list, canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COLOR_POS = "#AE3030"  # Imprint red: positive SHAP (pushes prediction up)
COLOR_NEG = "#4467A3"  # Imprint blue: negative SHAP (pushes prediction down)
LABEL_SHARE = 0.11  # a bar shorter than this share of the largest |SHAP| carries its label outside

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP_VALUE = "SHAP value"  # role: shap_value
BASE_VALUE = "Base value E[f(x)]"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# Credit loan approval model, one applicant's explanation; the base value repeats on every row
df = pd.DataFrame(
    {
        FEATURE: [
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
        ],
        SHAP_VALUE: [0.24, -0.18, 0.15, 0.12, -0.10, -0.08, 0.06, 0.04, 0.03, -0.02],
        BASE_VALUE: [0.42] * 10,
    }
)

# Plot: reads only df and the constants above
# Largest |SHAP| at the top; matplotlib draws y from the bottom, so sort ascending
# A feature without a SHAP value has no segment in the chain, so it is skipped
table = df.dropna(subset=[SHAP_VALUE])
table = table.reindex(table[SHAP_VALUE].abs().sort_values(kind="stable").index).reset_index(drop=True)
shap_values = table[SHAP_VALUE].to_numpy(dtype=float)
base_value = float(df[BASE_VALUE].dropna().iloc[0])
final_value = base_value + float(shap_values.sum())
n = len(table)
y_pos = np.arange(n)

# Running totals from the bottom bar upwards, starting at the base value
cum_after = base_value + np.cumsum(shap_values)
cum_before = cum_after - shap_values
bar_lefts = np.minimum(cum_before, cum_after)
bar_widths = np.abs(shap_values)
bar_colors = [COLOR_POS if sv >= 0 else COLOR_NEG for sv in shap_values]

title = "Credit Approval · shap-waterfall · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_axisbelow(True)

ax.barh(y_pos, bar_widths, left=bar_lefts, color=bar_colors, height=0.55, edgecolor=PAGE_BG, linewidth=0.8, zorder=3)

# Connectors: a dotted segment at each running total, bridging the gap to the next bar
for i in range(n - 1):
    ax.plot(
        [cum_after[i], cum_after[i]],
        [y_pos[i] + 0.32, y_pos[i + 1] - 0.32],
        color=INK_MUTED,
        linewidth=0.7,
        linestyle="dotted",
        alpha=0.7,
        zorder=2,
    )

# Reference lines for base value and final prediction
ax.axvline(base_value, color=INK_MUTED, linewidth=0.8, linestyle="--", alpha=0.6)
ax.axvline(final_value, color=INK_SOFT, linewidth=1.0, linestyle="--", alpha=0.7)

# SHAP value labels: inside wide bars, beside narrow ones
x_span = float(max(cum_after.max(), cum_before.max()) - bar_lefts.min())
label_gap = 0.012 * x_span
label_threshold = LABEL_SHARE * bar_widths.max()
for i, (sv, left, width) in enumerate(zip(shap_values, bar_lefts, bar_widths, strict=True)):
    txt = f"+{sv:.2f}" if sv > 0 else f"{sv:.2f}"
    if width >= label_threshold:
        ax.text(
            left + width / 2,
            y_pos[i],
            txt,
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            color="white",
            zorder=5,
        )
    else:
        positive = sv > 0
        ax.text(
            left + width + label_gap if positive else left - label_gap,
            y_pos[i],
            txt,
            ha="left" if positive else "right",
            va="center",
            fontsize=7,
            fontweight="bold",
            color=COLOR_POS if positive else COLOR_NEG,
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
    fontsize=7,
    color=INK_MUTED,
    bbox={
        "facecolor": ELEVATED_BG,
        "edgecolor": INK_MUTED,
        "boxstyle": "round,pad=0.35",
        "alpha": 0.9,
        "linewidth": 0.6,
    },
)
ax.text(
    final_value,
    top_y,
    f"f(x) = {final_value:.2f}",
    ha="center",
    va="bottom",
    fontsize=7,
    fontweight="bold",
    color=INK,
    bbox={
        "facecolor": ELEVATED_BG,
        "edgecolor": INK_SOFT,
        "boxstyle": "round,pad=0.35",
        "alpha": 0.9,
        "linewidth": 0.6,
    },
)

# Style
ax.set_yticks(y_pos, table[FEATURE])
ax.set_xlabel("Loan Approval Probability", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)

all_x = np.concatenate([bar_lefts, bar_lefts + bar_widths, [base_value, final_value]])
ax.set_xlim(all_x.min() - 0.1 * x_span, all_x.max() + 0.15 * x_span)
ax.set_ylim(-0.6, n + 0.9)

ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT, length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

ax.xaxis.grid(True, alpha=0.10, linewidth=0.5, color=INK)

# Legend
pos_patch = mpatches.Patch(color=COLOR_POS, label="Positive contribution")
neg_patch = mpatches.Patch(color=COLOR_NEG, label="Negative contribution")
leg = ax.legend(handles=[pos_patch, neg_patch], fontsize=8, loc="lower right", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
