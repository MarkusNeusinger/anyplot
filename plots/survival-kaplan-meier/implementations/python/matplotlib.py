""" pyplots.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Clinical trial survival data for two treatment groups
np.random.seed(42)

# Generate realistic survival times (exponential-like distribution)
n_per_group = 80

# Treatment group (better survival)
treatment_times = np.random.exponential(scale=24, size=n_per_group)
treatment_times = np.clip(treatment_times, 0.5, 60)  # Cap at 60 months
treatment_censored = np.random.binomial(1, 0.25, n_per_group)  # 25% censored
treatment_events = 1 - treatment_censored

# Control group (worse survival)
control_times = np.random.exponential(scale=16, size=n_per_group)
control_times = np.clip(control_times, 0.5, 60)
control_censored = np.random.binomial(1, 0.20, n_per_group)  # 20% censored
control_events = 1 - control_censored

# Kaplan-Meier calculation for Treatment group
order = np.argsort(treatment_times)
treat_t_sorted = treatment_times[order]
treat_e_sorted = treatment_events[order]
treat_unique = np.unique(treat_t_sorted[treat_e_sorted == 1])

treat_time_pts = [0.0]
treat_surv_probs = [1.0]
treat_std_errs = [0.0]
treat_surv = 1.0
treat_var = 0.0

for t in treat_unique:
    n_risk = np.sum(treat_t_sorted >= t)
    d = np.sum((treat_t_sorted == t) & (treat_e_sorted == 1))
    if n_risk > 0 and d > 0:
        treat_surv *= (n_risk - d) / n_risk
        if n_risk > d:
            treat_var += d / (n_risk * (n_risk - d))
    treat_time_pts.append(t)
    treat_surv_probs.append(treat_surv)
    treat_std_errs.append(np.sqrt(treat_var) * treat_surv if treat_surv > 0 else 0)

treat_times_km = np.array(treat_time_pts)
treat_surv_km = np.array(treat_surv_probs)
treat_se_km = np.array(treat_std_errs)

# Kaplan-Meier calculation for Control group
order = np.argsort(control_times)
ctrl_t_sorted = control_times[order]
ctrl_e_sorted = control_events[order]
ctrl_unique = np.unique(ctrl_t_sorted[ctrl_e_sorted == 1])

ctrl_time_pts = [0.0]
ctrl_surv_probs = [1.0]
ctrl_std_errs = [0.0]
ctrl_surv = 1.0
ctrl_var = 0.0

for t in ctrl_unique:
    n_risk = np.sum(ctrl_t_sorted >= t)
    d = np.sum((ctrl_t_sorted == t) & (ctrl_e_sorted == 1))
    if n_risk > 0 and d > 0:
        ctrl_surv *= (n_risk - d) / n_risk
        if n_risk > d:
            ctrl_var += d / (n_risk * (n_risk - d))
    ctrl_time_pts.append(t)
    ctrl_surv_probs.append(ctrl_surv)
    ctrl_std_errs.append(np.sqrt(ctrl_var) * ctrl_surv if ctrl_surv > 0 else 0)

ctrl_times_km = np.array(ctrl_time_pts)
ctrl_surv_km = np.array(ctrl_surv_probs)
ctrl_se_km = np.array(ctrl_std_errs)

# Get censored observation times for tick marks
treat_censor_times = treatment_times[treatment_events == 0]
ctrl_censor_times = control_times[control_events == 0]

# Interpolate survival at censored times for tick marks
treat_censor_surv = np.interp(treat_censor_times, treat_times_km, treat_surv_km)
ctrl_censor_surv = np.interp(ctrl_censor_times, ctrl_times_km, ctrl_surv_km)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Python colors
treatment_color = "#306998"
control_color = "#FFD43B"

# Treatment group curve with CI
ax.step(treat_times_km, treat_surv_km, where="post", color=treatment_color, linewidth=3, label="Treatment Group")
treat_upper = np.clip(treat_surv_km + 1.96 * treat_se_km, 0, 1)
treat_lower = np.clip(treat_surv_km - 1.96 * treat_se_km, 0, 1)
ax.fill_between(treat_times_km, treat_lower, treat_upper, step="post", alpha=0.2, color=treatment_color)

# Control group curve with CI
ax.step(ctrl_times_km, ctrl_surv_km, where="post", color=control_color, linewidth=3, label="Control Group")
ctrl_upper = np.clip(ctrl_surv_km + 1.96 * ctrl_se_km, 0, 1)
ctrl_lower = np.clip(ctrl_surv_km - 1.96 * ctrl_se_km, 0, 1)
ax.fill_between(ctrl_times_km, ctrl_lower, ctrl_upper, step="post", alpha=0.3, color=control_color)

# Censored observation tick marks
ax.scatter(treat_censor_times, treat_censor_surv, marker="|", s=400, color=treatment_color, linewidth=2, zorder=5)
ax.scatter(ctrl_censor_times, ctrl_censor_surv, marker="|", s=400, color="#CC9A00", linewidth=2, zorder=5)

# Calculate median survival times
treat_median_idx = np.where(treat_surv_km <= 0.5)[0]
ctrl_median_idx = np.where(ctrl_surv_km <= 0.5)[0]

treat_median = treat_times_km[treat_median_idx[0]] if len(treat_median_idx) > 0 else None
ctrl_median = ctrl_times_km[ctrl_median_idx[0]] if len(ctrl_median_idx) > 0 else None

# Add median survival annotation lines
if treat_median:
    ax.axhline(y=0.5, color="gray", linestyle=":", linewidth=1.5, alpha=0.5)
    ax.axvline(x=treat_median, color=treatment_color, linestyle=":", linewidth=1.5, alpha=0.7)
if ctrl_median:
    ax.axvline(x=ctrl_median, color="#CC9A00", linestyle=":", linewidth=1.5, alpha=0.7)

# Add median text
median_text = ""
if treat_median:
    median_text += f"Treatment median: {treat_median:.1f} mo"
if ctrl_median:
    median_text += f"\nControl median: {ctrl_median:.1f} mo"

ax.text(
    0.98,
    0.02,
    median_text.strip(),
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "gray", "alpha": 0.8},
)

# Styling
ax.set_xlabel("Time (months)", fontsize=20)
ax.set_ylabel("Survival Probability", fontsize=20)
ax.set_title("survival-kaplan-meier · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 65)
ax.set_ylim(0, 1.05)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
