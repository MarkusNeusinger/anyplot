""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theme and context
sns.set_theme(style="white", context="talk", font_scale=1.1)
palette = sns.color_palette("muted")
stem_color = "#306998"
ci_color = palette[1]

# Data: ARMA(1,1) process simulating monthly airline passenger residuals
np.random.seed(42)
n_obs = 200
ar1_coeff = 0.7
ma1_coeff = 0.4
noise = np.random.randn(n_obs)
series = np.zeros(n_obs)
series[0] = noise[0]
for t in range(1, n_obs):
    series[t] = ar1_coeff * series[t - 1] + noise[t] + ma1_coeff * noise[t - 1]

# Compute ACF
n_lags = 35
mean = np.mean(series)
var = np.sum((series - mean) ** 2)
acf_values = np.array([np.sum((series[: n_obs - k] - mean) * (series[k:] - mean)) / var for k in range(n_lags + 1)])

# Compute PACF via Durbin-Levinson recursion
pacf_values = np.zeros(n_lags + 1)
pacf_values[0] = 1.0
pacf_values[1] = acf_values[1]
phi = np.zeros((n_lags + 1, n_lags + 1))
phi[1, 1] = acf_values[1]
for k in range(2, n_lags + 1):
    num = acf_values[k] - np.sum(phi[k - 1, 1:k] * acf_values[k - 1 : 0 : -1])
    den = 1.0 - np.sum(phi[k - 1, 1:k] * acf_values[1:k])
    phi[k, k] = num / den if den != 0 else 0
    for j in range(1, k):
        phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
    pacf_values[k] = phi[k, k]

lags_acf = np.arange(0, n_lags + 1)
lags_pacf = np.arange(1, n_lags + 1)
conf_bound = 1.96 / np.sqrt(n_obs)

# Build DataFrames for seaborn
acf_df = pd.DataFrame({"Lag": lags_acf, "Correlation": acf_values})
pacf_df = pd.DataFrame({"Lag": lags_pacf, "Correlation": pacf_values[1:]})

# Identify significant lags (exceed confidence bounds)
sig_acf = acf_df[(acf_df["Lag"] > 0) & (acf_df["Correlation"].abs() > conf_bound)]
sig_pacf = pacf_df[pacf_df["Correlation"].abs() > conf_bound]

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True)

stem_width = 2.5
marker_size = 60

# ACF subplot - stems via vlines, markers via seaborn scatterplot
ax1.vlines(acf_df["Lag"], 0, acf_df["Correlation"], colors=stem_color, linewidth=stem_width)
sns.scatterplot(
    data=acf_df,
    x="Lag",
    y="Correlation",
    color=stem_color,
    s=marker_size,
    zorder=5,
    edgecolor="white",
    linewidth=0.5,
    ax=ax1,
    legend=False,
)
ax1.axhline(y=0, color="#333333", linewidth=0.8)
ax1.axhline(y=conf_bound, color=ci_color, linestyle="--", linewidth=1.5, alpha=0.8)
ax1.axhline(y=-conf_bound, color=ci_color, linestyle="--", linewidth=1.5, alpha=0.8)
ax1.fill_between([-0.5, n_lags + 0.5], -conf_bound, conf_bound, color=ci_color, alpha=0.08)

# Highlight the first significant ACF lag with annotation
if len(sig_acf) > 0:
    first_sig = sig_acf.iloc[0]
    ax1.annotate(
        f"lag {int(first_sig['Lag'])}: {first_sig['Correlation']:.2f}",
        xy=(first_sig["Lag"], first_sig["Correlation"]),
        xytext=(first_sig["Lag"] + 4, first_sig["Correlation"] + 0.12),
        fontsize=13,
        color=stem_color,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": stem_color, "lw": 1.5},
    )

# PACF subplot
ax2.vlines(pacf_df["Lag"], 0, pacf_df["Correlation"], colors=stem_color, linewidth=stem_width)
sns.scatterplot(
    data=pacf_df,
    x="Lag",
    y="Correlation",
    color=stem_color,
    s=marker_size,
    zorder=5,
    edgecolor="white",
    linewidth=0.5,
    ax=ax2,
    legend=False,
)
ax2.axhline(y=0, color="#333333", linewidth=0.8)
ax2.axhline(y=conf_bound, color=ci_color, linestyle="--", linewidth=1.5, alpha=0.8)
ax2.axhline(y=-conf_bound, color=ci_color, linestyle="--", linewidth=1.5, alpha=0.8)
ax2.fill_between([-0.5, n_lags + 0.5], -conf_bound, conf_bound, color=ci_color, alpha=0.08)

# Highlight dominant PACF spike
if len(sig_pacf) > 0:
    first_sig_p = sig_pacf.iloc[0]
    ax2.annotate(
        f"lag {int(first_sig_p['Lag'])}: {first_sig_p['Correlation']:.2f}",
        xy=(first_sig_p["Lag"], first_sig_p["Correlation"]),
        xytext=(first_sig_p["Lag"] + 4, first_sig_p["Correlation"] + 0.12),
        fontsize=13,
        color=stem_color,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": stem_color, "lw": 1.5},
    )

# Style
fig.suptitle("acf-pacf · seaborn · pyplots.ai", fontsize=24, fontweight="medium", y=0.97)

ax1.set_ylabel("Autocorrelation (ACF)", fontsize=20)
ax2.set_ylabel("Partial Autocorrelation (PACF)", fontsize=20)
ax2.set_xlabel("Lag (months)", fontsize=20)

for ax in (ax1, ax2):
    ax.tick_params(axis="both", labelsize=16)
    ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
    ax.set_xlim(-0.5, n_lags + 0.5)

sns.despine(fig=fig)

plt.tight_layout()
plt.subplots_adjust(top=0.92)

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
