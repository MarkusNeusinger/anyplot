"""anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MEDIAN_LEVEL = 0.5  # survival probability that defines the median survival time
Z_95 = 1.96  # two-sided 95% confidence interval

# Columns: set these to your table's column names
TIME = "Time (months)"  # role: time
EVENT = "Event (1 = event, 0 = censored)"  # role: event
GROUP = "Group"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
np.random.seed(42)
n_treatment = 80
treatment_times = np.clip(np.random.exponential(scale=24, size=n_treatment), 0.5, 36)
treatment_censored = np.random.binomial(1, 0.35, n_treatment)
n_control = 80
control_times = np.clip(np.random.exponential(scale=16, size=n_control), 0.5, 36)
control_censored = np.random.binomial(1, 0.3, n_control)
df = pd.DataFrame(
    {
        TIME: np.concatenate([treatment_times, control_times]),
        EVENT: np.concatenate([1 - treatment_censored, 1 - control_censored]),
        GROUP: ["Treatment"] * n_treatment + ["Control"] * n_control,
    }
)


# Plot: reads only df and the constants above
def compute_km(times, events):
    """Kaplan-Meier curve with 95% log-log-style confidence limits and censoring marks."""
    order = np.argsort(times)
    times = times[order]
    events = events[order]

    survival, time_points, ci_lower, ci_upper = [1.0], [0.0], [1.0], [1.0]
    var_sum = 0.0
    for t in np.unique(times[events == 1]):
        at_risk = np.sum(times >= t)
        d = np.sum((times == t) & (events == 1))
        survival.append(survival[-1] * (1 - d / at_risk))
        time_points.append(t)
        if at_risk > d:
            var_sum += d / (at_risk * (at_risk - d))
        se = np.sqrt(var_sum)
        log_s = np.log(survival[-1]) if survival[-1] > 0 else -np.inf
        ci_factor = Z_95 * se / abs(log_s) if log_s != 0 else 0
        ci_lower.append(survival[-1] ** np.exp(ci_factor))
        ci_upper.append(survival[-1] ** np.exp(-ci_factor))

    # Censored observations sit on the curve at their own time
    cens_t = times[events == 0]
    cens_s = np.array(survival)[np.searchsorted(time_points[1:], cens_t, side="right")]
    return np.array(time_points), np.array(survival), np.array(ci_lower), np.array(ci_upper), cens_t, cens_s


def to_steps(x, y):
    """Convert point data to a step function (flat, then vertical drop)."""
    return np.repeat(x, 2)[1:], np.repeat(y, 2)[:-1]


groups = list(df[GROUP].unique())
x_max = df[TIME].max() * 1.05

p = figure(
    width=3200,
    height=1800,
    title="survival-kaplan-meier · python · bokeh · anyplot.ai",
    x_axis_label=TIME,
    y_axis_label="Survival Probability",
    x_range=(0, x_max),
    y_range=(0, 1.05),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

for i, group in enumerate(groups):
    rows = df[df[GROUP] == group]
    color = IMPRINT_PALETTE[i]
    t, s, lo, up, cens_t, cens_s = compute_km(rows[TIME].to_numpy(), rows[EVENT].to_numpy())
    x_step, s_step = to_steps(t, s)
    _, lo_step = to_steps(t, lo)
    _, up_step = to_steps(t, up)

    # Confidence band stepping with its curve
    band = ColumnDataSource(
        {"x": np.concatenate([x_step, x_step[::-1]]), "y": np.concatenate([lo_step, up_step[::-1]])}
    )
    p.patch(x="x", y="y", source=band, fill_color=color, fill_alpha=0.15, line_alpha=0)

    p.line(x_step, s_step, line_color=color, line_width=3, legend_label=f"{group} (n={len(rows)})")

    # Censored observations as tick marks on the curve
    p.scatter(cens_t, cens_s, marker="dash", size=20, angle=np.pi / 2, line_color=color, line_width=3)

# Median survival reference line
p.add_layout(Span(location=MEDIAN_LEVEL, dimension="width", line_color=INK_SOFT, line_width=2, line_dash="dashed"))

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "50pt"

for axis in (p.xaxis, p.yaxis):
    axis.axis_label_text_color = INK
    axis.axis_label_text_font_size = "42pt"
    axis.major_label_text_color = INK_SOFT
    axis.major_label_text_font_size = "34pt"
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.location = "bottom_left"
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Save
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
