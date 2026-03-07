""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


# Data
np.random.seed(42)
sample_rate = 22050
duration = 1.0
num_samples = int(sample_rate * duration)
time = np.linspace(0, duration, num_samples)

base_freq = 220
segments = [
    np.linspace(0, 1, int(num_samples * 0.05)),
    np.ones(int(num_samples * 0.15)),
    np.exp(-3 * np.linspace(0, 1, int(num_samples * 0.3))),
    np.linspace(0.05, 0.8, int(num_samples * 0.1)),
    np.ones(int(num_samples * 0.1)),
    np.exp(-2 * np.linspace(0, 1, int(num_samples * 0.3))),
]
amplitude_envelope = np.concatenate(segments)
if len(amplitude_envelope) < num_samples:
    amplitude_envelope = np.pad(
        amplitude_envelope, (0, num_samples - len(amplitude_envelope)), constant_values=amplitude_envelope[-1]
    )
amplitude_envelope = amplitude_envelope[:num_samples]

signal = (
    0.6 * np.sin(2 * np.pi * base_freq * time)
    + 0.25 * np.sin(2 * np.pi * base_freq * 2 * time)
    + 0.1 * np.sin(2 * np.pi * base_freq * 3 * time)
    + 0.05 * np.sin(2 * np.pi * base_freq * 5 * time)
)
signal *= amplitude_envelope
signal += np.random.normal(0, 0.01, num_samples)
signal = np.clip(signal, -1.0, 1.0)

# Downsample for smooth envelope rendering
chunk_size = 80
num_chunks = num_samples // chunk_size
time_chunks = time[: num_chunks * chunk_size].reshape(num_chunks, chunk_size)
signal_chunks = signal[: num_chunks * chunk_size].reshape(num_chunks, chunk_size)

env_time = time_chunks.mean(axis=1)
env_max = signal_chunks.max(axis=1)
env_min = signal_chunks.min(axis=1)

# Smooth the envelope to remove oscillation jaggedness
kernel = np.ones(5) / 5
env_max = np.convolve(env_max, kernel, mode="same")
env_min = np.convolve(env_min, kernel, mode="same")

# Classify segments for storytelling: loud vs quiet regions
smooth_kernel = np.ones(15) / 15
rms = np.sqrt(np.convolve((env_max - env_min) ** 2, smooth_kernel, mode="same"))
rms_threshold = np.median(rms) * 1.1
segment_label = np.where(rms > rms_threshold, "Loud", "Quiet")

# Build a long-form DataFrame for seaborn envelope edges
df_env = pd.DataFrame(
    {
        "Time (seconds)": np.concatenate([env_time, env_time]),
        "Amplitude": np.concatenate([env_max, env_min]),
        "edge": ["upper"] * len(env_time) + ["lower"] * len(env_time),
    }
)

# Color palette for dynamics emphasis
dynamics_palette = {"Loud": "#306998", "Quiet": "#89ABD0"}

# Plot
sns.set_theme(
    style="whitegrid",
    context="talk",
    font_scale=1.2,
    rc={
        "grid.alpha": 0.15,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#444444",
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Fill quiet regions first (background layer), then loud on top
for label, color, alpha in [("Quiet", "#89ABD0", 0.3), ("Loud", "#306998", 0.55)]:
    mask = segment_label == label
    sections = np.ma.clump_unmasked(np.ma.masked_where(~mask, mask))
    for sl in sections:
        start = max(0, sl.start - 1)
        stop = min(len(env_time), sl.stop + 1)
        expanded = slice(start, stop)
        ax.fill_between(env_time[expanded], env_max[expanded], env_min[expanded], color=color, alpha=alpha, linewidth=0)

# Draw continuous envelope edges with seaborn lineplot
sns.lineplot(
    data=df_env,
    x="Time (seconds)",
    y="Amplitude",
    hue="edge",
    palette={"upper": "#306998", "lower": "#306998"},
    linewidth=1.5,
    alpha=0.85,
    legend=False,
    ax=ax,
)

# Zero-line
ax.axhline(y=0, color="#888888", linewidth=1.0, alpha=0.4, zorder=1)

# Storytelling annotations for dynamic sections
ax.annotate(
    "Attack + Sustain", xy=(0.10, 0.76), fontsize=13, color="#1E4264", fontstyle="italic", ha="center", va="bottom"
)
ax.annotate("Decay", xy=(0.38, 0.22), fontsize=13, color="#5A84A8", fontstyle="italic", ha="center", va="bottom")
ax.annotate(
    "Second Phrase", xy=(0.72, 0.65), fontsize=13, color="#1E4264", fontstyle="italic", ha="center", va="bottom"
)

# Legend for dynamics
legend_elements = [
    Patch(facecolor="#306998", alpha=0.55, label="Loud"),
    Patch(facecolor="#89ABD0", alpha=0.3, label="Quiet"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=14, framealpha=0.8)

# Style
ax.set_xlabel("Time (seconds)", fontsize=20)
ax.set_ylabel("Amplitude", fontsize=20)
ax.set_title("waveform-audio · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(-1.05, 1.05)
ax.set_xlim(0, duration)
sns.despine(ax=ax)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
