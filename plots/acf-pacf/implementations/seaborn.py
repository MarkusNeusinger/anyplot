"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
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

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True)

color = "#306998"
stem_width = 2.5
marker_size = 5

markerline1, stemlines1, baseline1 = ax1.stem(lags_acf, acf_values)
plt.setp(stemlines1, linewidth=stem_width, color=color)
plt.setp(markerline1, markersize=marker_size, color=color, zorder=5)
plt.setp(baseline1, linewidth=0.8, color="#333333")

ax1.axhline(y=conf_bound, color="#D95319", linestyle="--", linewidth=1.5, alpha=0.8)
ax1.axhline(y=-conf_bound, color="#D95319", linestyle="--", linewidth=1.5, alpha=0.8)
ax1.fill_between([-0.5, n_lags + 0.5], -conf_bound, conf_bound, color="#D95319", alpha=0.08)

markerline2, stemlines2, baseline2 = ax2.stem(lags_pacf, pacf_values[1:])
plt.setp(stemlines2, linewidth=stem_width, color=color)
plt.setp(markerline2, markersize=marker_size, color=color, zorder=5)
plt.setp(baseline2, linewidth=0.8, color="#333333")

ax2.axhline(y=conf_bound, color="#D95319", linestyle="--", linewidth=1.5, alpha=0.8)
ax2.axhline(y=-conf_bound, color="#D95319", linestyle="--", linewidth=1.5, alpha=0.8)
ax2.fill_between([-0.5, n_lags + 0.5], -conf_bound, conf_bound, color="#D95319", alpha=0.08)

# Style
fig.suptitle("acf-pacf · seaborn · pyplots.ai", fontsize=24, fontweight="medium", y=0.97)

ax1.set_ylabel("ACF", fontsize=20)
ax2.set_ylabel("PACF", fontsize=20)
ax2.set_xlabel("Lag", fontsize=20)

for ax in (ax1, ax2):
    ax.tick_params(axis="both", labelsize=16)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
    ax.set_xlim(-0.5, n_lags + 0.5)

plt.tight_layout()
plt.subplots_adjust(top=0.92)

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
