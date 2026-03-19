"""pyplots.ai
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


def _ecg_beat(t_arr, bc, hri, p_amp=0.15, p_width=0.025, t_amp=0.30, t_width=0.04):
    p = _gauss(t_arr, bc - 0.16 * hri, p_width, p_amp)
    q = _gauss(t_arr, bc - 0.04 * hri, 0.007, -0.12)
    r = _gauss(t_arr, bc, 0.007, 1.2)
    s = _gauss(t_arr, bc + 0.025 * hri, 0.007, -0.20)
    st = _gauss(t_arr, bc + 0.08 * hri, 0.02, 0.03)
    tw = _gauss(t_arr, bc + 0.22 * hri, t_width, t_amp)
    return p + q + r + s + st + tw


# Lead-specific morphology: (scale, p_amp, p_width, t_amp, t_width)
lead_params = {
    "I": (0.55, 0.12, 0.025, 0.25, 0.04),
    "II": (1.0, 0.18, 0.028, 0.35, 0.045),
    "III": (0.45, 0.08, 0.022, 0.18, 0.038),
    "aVR": (-0.65, -0.10, 0.024, -0.22, 0.042),
    "aVL": (0.25, 0.06, 0.020, 0.10, 0.035),
    "aVF": (0.70, 0.14, 0.026, 0.28, 0.042),
    "V1": (-0.75, 0.08, 0.020, -0.18, 0.038),
    "V2": (-0.40, 0.10, 0.022, 0.12, 0.040),
    "V3": (0.35, 0.12, 0.024, 0.22, 0.042),
    "V4": (0.95, 0.15, 0.026, 0.32, 0.044),
    "V5": (0.70, 0.13, 0.025, 0.28, 0.043),
    "V6": (0.50, 0.11, 0.024, 0.22, 0.040),
}

# Standard clinical 3×4 grid order (3 rows, 4 columns)
# Row 0: I, aVR, V1, V4 | Row 1: II, aVL, V2, V5 | Row 2: III, aVF, V3, V6
grid_order = ["I", "aVR", "V1", "V4", "II", "aVL", "V2", "V5", "III", "aVF", "V3", "V6"]

frames = []
for lead_name in grid_order:
    scale, p_a, p_w, t_a, t_w = lead_params[lead_name]
    signal = np.zeros_like(t)
    for bc in beat_centers:
        signal += scale * _ecg_beat(t, bc, hr_interval, p_amp=p_a, p_width=p_w, t_amp=t_a, t_width=t_w)
    signal += np.random.normal(0, 0.008, n_samples)
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
y_major = np.arange(-1.5, 1.6, 1.0).tolist()
y_minor = np.arange(-1.5, 1.6, 0.5).tolist()

plot = (
    ggplot(df, aes(x="time", y="voltage"))
    + geom_line(color=signal_color, size=0.7)
    + geom_line(aes(x="time", y="voltage"), data=cal_df, color=signal_color, size=0.9)
    + geom_text(aes(label="label"), data=label_df, size=15, ha="left", va="top", fontweight="bold", color="#333333")
    + geom_text(aes(label="label"), data=cal_label_df, size=12, ha="center", va="top", color="#333333")
    + facet_wrap("lead", ncol=4)
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
