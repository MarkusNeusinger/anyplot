""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_line,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data — synthetic ECG using Gaussian pulse model
np.random.seed(42)

sampling_rate = 500
duration = 2.5
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
n_samples = len(t)

hr_bpm = 72
hr_interval = 60.0 / hr_bpm
beat_centers = np.arange(hr_interval * 0.35, duration, hr_interval)


def _gauss(t_arr, center, width, amplitude):
    return amplitude * np.exp(-((t_arr - center) ** 2) / (2 * width**2))


def _ecg_beat(t_arr, bc, hri):
    p = _gauss(t_arr, bc - 0.16 * hri, 0.025, 0.15)
    q = _gauss(t_arr, bc - 0.04 * hri, 0.007, -0.12)
    r = _gauss(t_arr, bc, 0.007, 1.2)
    s = _gauss(t_arr, bc + 0.025 * hri, 0.007, -0.20)
    st = _gauss(t_arr, bc + 0.08 * hri, 0.02, 0.03)
    tw = _gauss(t_arr, bc + 0.22 * hri, 0.04, 0.30)
    return p + q + r + s + st + tw


base_signal = np.zeros_like(t)
for bc in beat_centers:
    base_signal += _ecg_beat(t, bc, hr_interval)

# Lead-specific morphology transforms
lead_params = {
    "I": 0.55,
    "II": 1.0,
    "III": 0.45,
    "aVR": -0.65,
    "aVL": 0.25,
    "aVF": 0.70,
    "V1": -0.75,
    "V2": -0.40,
    "V3": 0.35,
    "V4": 0.95,
    "V5": 0.70,
    "V6": 0.50,
}

# Standard clinical 3×4 grid order (3 rows, 4 columns)
# Row 0: I, aVR, V1, V4 | Row 1: II, aVL, V2, V5 | Row 2: III, aVF, V3, V6
grid_order = ["I", "aVR", "V1", "V4", "II", "aVL", "V2", "V5", "III", "aVF", "V3", "V6"]

frames = []
for lead_name in grid_order:
    scale = lead_params[lead_name]
    signal = base_signal * scale + np.random.normal(0, 0.008, n_samples)
    frames.append(pd.DataFrame({"time": t, "voltage": signal, "lead": lead_name}))

df = pd.concat(frames, ignore_index=True)
df["lead"] = pd.Categorical(df["lead"], categories=grid_order, ordered=True)

# Lead label positions (top-left of each facet)
label_df = pd.DataFrame(
    {
        "time": [0.08] * 12,
        "voltage": [1.35] * 12,
        "lead": pd.Categorical(grid_order, categories=grid_order, ordered=True),
        "label": grid_order,
    }
)

# 1mV calibration pulse — shown in the first facet (Lead I)
cal_t = [0.0, 0.0, 0.05, 0.05]
cal_v = [0.0, 1.0, 1.0, 0.0]
cal_df = pd.DataFrame(
    {"time": cal_t, "voltage": cal_v, "lead": pd.Categorical(["I"] * 4, categories=grid_order, ordered=True)}
)
# Calibration label
cal_label_df = pd.DataFrame(
    {
        "time": [0.025],
        "voltage": [-0.25],
        "lead": pd.Categorical(["I"], categories=grid_order, ordered=True),
        "label": ["1 mV"],
    }
)

# Plot
ecg_paper = "#FFF5EE"
major_grid = "#E8A090"
minor_grid = "#F0C8BC"
signal_color = "#1a1a2e"

x_major = np.arange(0, duration + 0.01, 0.5).tolist()
x_minor = np.arange(0, duration + 0.01, 0.1).tolist()
y_major = np.arange(-2.0, 2.1, 0.5).tolist()
y_minor = np.arange(-2.0, 2.1, 0.1).tolist()

plot = (
    ggplot(df, aes(x="time", y="voltage"))
    + geom_line(color=signal_color, size=0.7)
    + geom_line(aes(x="time", y="voltage"), data=cal_df, color=signal_color, size=0.9)
    + geom_text(aes(label="label"), data=label_df, size=13, ha="left", va="top", fontweight="bold", color="#333333")
    + geom_text(aes(label="label"), data=cal_label_df, size=9, ha="center", va="top", color="#333333")
    + facet_wrap("lead", ncol=4, scales="free_y")
    + scale_x_continuous(breaks=x_major, minor_breaks=x_minor, limits=(0, duration), expand=(0.01, 0.01))
    + scale_y_continuous(breaks=y_major, minor_breaks=y_minor, limits=(-1.6, 1.6), expand=(0, 0))
    + labs(title="ecg-twelve-lead · plotnine · pyplots.ai", x="Time (s)", y="Voltage (mV)")
    + theme(
        figure_size=(16, 9),
        panel_background=element_rect(fill=ecg_paper),
        plot_background=element_rect(fill="white"),
        panel_grid_major=element_line(color=major_grid, size=0.5),
        panel_grid_minor=element_line(color=minor_grid, size=0.25),
        strip_background=element_blank(),
        strip_text=element_blank(),
        text=element_text(size=16),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16, color="#666666"),
        plot_title=element_text(size=24, weight="bold", margin={"b": 12}),
        panel_spacing_x=0.06,
        panel_spacing_y=0.04,
        axis_ticks=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
