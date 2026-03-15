"""pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

studies = [
    "Adams 2018",
    "Baker 2019",
    "Chen 2017",
    "Diaz 2020",
    "Evans 2016",
    "Fischer 2021",
    "Garcia 2019",
    "Hughes 2018",
    "Ibrahim 2020",
    "Jones 2017",
    "Kim 2021",
    "Lee 2019",
    "Martinez 2020",
    "Novak 2018",
    "O'Brien 2022",
]

n_studies = len(studies)
true_effect = -0.35

std_errors = np.concatenate(
    [np.random.uniform(0.05, 0.15, 5), np.random.uniform(0.15, 0.30, 6), np.random.uniform(0.30, 0.50, 4)]
)

effect_sizes = true_effect + np.random.normal(0, 1, n_studies) * std_errors
effect_sizes[-2] += 0.25
effect_sizes[-1] += 0.30

summary_effect = np.average(effect_sizes, weights=1 / std_errors**2)

df = pd.DataFrame({"effect_size": effect_sizes, "std_error": std_errors, "study": studies})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

se_range = np.linspace(0, 0.55, 300)
ci_left = summary_effect - 1.96 * se_range
ci_right = summary_effect + 1.96 * se_range

ax.fill_betweenx(se_range, ci_left, ci_right, color="#306998", alpha=0.06)
ax.plot(ci_left, se_range, color="#306998", linewidth=1.5, linestyle="--", alpha=0.5)
ax.plot(ci_right, se_range, color="#306998", linewidth=1.5, linestyle="--", alpha=0.5)

ax.axvline(x=summary_effect, color="#306998", linewidth=2.5, alpha=0.7, label=f"Summary effect ({summary_effect:.2f})")

ax.axvline(x=0, color="#888888", linewidth=1.5, linestyle=":", alpha=0.6, label="Null effect (0)")

sns.scatterplot(
    data=df,
    x="effect_size",
    y="std_error",
    s=280,
    color="#306998",
    edgecolor="white",
    linewidth=1.2,
    alpha=0.85,
    zorder=5,
    ax=ax,
)

# Style
ax.invert_yaxis()
ax.set_xlabel("Log Odds Ratio (Drug vs Placebo)", fontsize=20)
ax.set_ylabel("Standard Error", fontsize=20)
ax.set_title("funnel-meta-analysis · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=16, frameon=False, loc="lower left")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
