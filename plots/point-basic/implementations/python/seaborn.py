"""anyplot.ai
point-basic: Point Estimate Plot
Library: seaborn 0.13.2 | Python 3.13.13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint palette position 1: first series
REF_COLOR = "#C475FD"  # Imprint palette position 2: reference line

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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)


# Constants
N_SAMPLES = 80
N_BOOT = 2000
CI_LEVEL = 95

# Columns
ENDPOINT = "API Endpoint"  # role: category
ESTIMATE = "Response Time (ms)"  # role: estimate
LOWER = "Lower 95% CI (ms)"  # role: lower_bound
UPPER = "Upper 95% CI (ms)"  # role: upper_bound

# Data: API endpoint response times (ms), log-normal for realistic right-skewed latency,
# summarised to a mean and a bootstrap confidence interval per endpoint
rng = np.random.default_rng(42)
endpoints = ["Auth Service", "Search API", "Product Catalog", "Cart Service", "Payment API", "Analytics"]
lognorm_params = [(3.8, 0.40), (4.7, 0.50), (4.4, 0.35), (4.0, 0.45), (4.5, 0.30), (5.1, 0.60)]
tail = (100 - CI_LEVEL) / 2

rows = []
for endpoint, (mu, sigma) in zip(endpoints, lognorm_params, strict=True):
    times = rng.lognormal(mu, sigma, N_SAMPLES)
    boot_means = rng.choice(times, size=(N_BOOT, N_SAMPLES)).mean(axis=1)
    lo, hi = np.percentile(boot_means, [tail, 100 - tail])
    rows.append({ENDPOINT: endpoint, ESTIMATE: times.mean(), LOWER: lo, UPPER: hi})

df = pd.DataFrame(rows).sort_values(ESTIMATE).reset_index(drop=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Reference line at the mean of the endpoint estimates
reference = df[ESTIMATE].mean()
ax.axvline(
    x=reference,
    color=REF_COLOR,
    linestyle="--",
    linewidth=1.25,
    alpha=0.85,
    label=f"Mean of endpoints ({reference:.0f} ms)",
    zorder=1,
)

# Intervals with caps, then seaborn markers on top
ax.errorbar(
    df[ESTIMATE],
    df[ENDPOINT],
    xerr=[df[ESTIMATE] - df[LOWER], df[UPPER] - df[ESTIMATE]],
    fmt="none",
    ecolor=BRAND,
    elinewidth=1.25,
    capsize=4,
    capthick=1.25,
    zorder=2,
)
sns.scatterplot(data=df, x=ESTIMATE, y=ENDPOINT, color=BRAND, s=60, edgecolor=PAGE_BG, linewidth=0.5, zorder=3, ax=ax)
ax.set_ylim(len(df) - 0.5, -0.5)

# Style
ax.set_xlabel(ESTIMATE, fontsize=10, color=INK)
ax.set_ylabel(ENDPOINT, fontsize=10, color=INK)
ax.set_title("point-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.xaxis.grid(True, alpha=0.10, linewidth=0.8)

ax.legend(fontsize=8, loc="upper right", frameon=True)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
