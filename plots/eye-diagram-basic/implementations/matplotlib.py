""" pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-17
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Data
np.random.seed(42)

n_traces = 400
samples_per_ui = 150
n_bits = 3

noise_sigma = 0.05
jitter_sigma = 0.03

bit_sequences = np.random.randint(0, 2, (n_traces, n_bits + 2))

all_time = []
all_voltage = []

for i in range(n_traces):
    bits = bit_sequences[i]
    t_full = np.linspace(-1, n_bits + 1, (n_bits + 2) * samples_per_ui)
    signal = np.zeros_like(t_full)

    for b in range(n_bits + 2):
        signal += bits[b] * (1 / (1 + np.exp(-20 * (t_full - b + 0.5))))
        if b > 0:
            signal -= bits[b - 1] * (1 / (1 + np.exp(-20 * (t_full - b + 0.5))))

    t_jittered = t_full + np.random.normal(0, jitter_sigma, len(t_full))

    noise = np.random.normal(0, noise_sigma, len(t_full))
    signal_noisy = signal + noise

    mask = (t_jittered >= 0) & (t_jittered <= 2)
    all_time.extend(t_jittered[mask])
    all_voltage.extend(signal_noisy[mask])

all_time = np.array(all_time)
all_voltage = np.array(all_voltage)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

heatmap_cmap = LinearSegmentedColormap.from_list(
    "eye_density", ["#0a0a2e", "#1a237e", "#306998", "#42a5f5", "#80deea", "#ffeb3b", "#ff9800", "#ff1744"]
)

h, xedges, yedges = np.histogram2d(all_time, all_voltage, bins=[300, 200], range=[[0, 2], [-0.3, 1.3]])

h_log = np.log1p(h.T)

ax.imshow(h_log, origin="lower", aspect="auto", extent=[0, 2, -0.3, 1.3], cmap=heatmap_cmap, interpolation="gaussian")

# Style
ax.set_xlabel("Time (UI)", fontsize=20)
ax.set_ylabel("Voltage (V)", fontsize=20)
ax.set_title("eye-diagram-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.set_facecolor("#0a0a2e")
fig.patch.set_facecolor("#0f0f23")

ax.spines["bottom"].set_color("#cccccc")
ax.spines["left"].set_color("#cccccc")
ax.tick_params(colors="#cccccc")
ax.xaxis.label.set_color("#cccccc")
ax.yaxis.label.set_color("#cccccc")
ax.title.set_color("#eeeeee")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
