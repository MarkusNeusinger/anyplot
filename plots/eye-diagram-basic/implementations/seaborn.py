"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d


# Data
np.random.seed(42)
n_traces = 400
samples_per_ui = 200
ui_span = 2
n_display = samples_per_ui * ui_span
noise_sigma = 0.05
jitter_sigma = 0.03
bw_filter_sigma = 12

all_time = []
all_voltage = []

t_ui = np.linspace(0, ui_span, n_display, endpoint=False)

for _ in range(n_traces):
    n_bits = 8
    bits = np.random.randint(0, 2, size=n_bits)
    samples_total = samples_per_ui * n_bits

    signal_raw = np.repeat(bits.astype(float), samples_per_ui)
    signal_smooth = gaussian_filter1d(signal_raw, sigma=bw_filter_sigma)

    jitter_shift = int(np.random.normal(0, jitter_sigma * samples_per_ui))
    signal_smooth = np.roll(signal_smooth, jitter_shift)

    signal_smooth += np.random.normal(0, noise_sigma, samples_total)

    start_bit = 3
    start_idx = start_bit * samples_per_ui
    end_idx = start_idx + n_display
    segment = signal_smooth[start_idx:end_idx]

    all_time.extend(t_ui.tolist())
    all_voltage.extend(segment.tolist())

all_time = np.array(all_time)
all_voltage = np.array(all_voltage)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

h, xedges, yedges = np.histogram2d(all_time, all_voltage, bins=[400, 250], range=[[0, 2], [-0.3, 1.3]])
h = h.T
h_smooth = gaussian_filter1d(h, sigma=0.7, axis=0)
h_smooth = gaussian_filter1d(h_smooth, sigma=0.7, axis=1)

cmap = plt.cm.inferno.copy()
cmap.set_under("black")

norm = mcolors.PowerNorm(gamma=0.35, vmin=1, vmax=h_smooth.max())

ax.imshow(
    h_smooth, origin="lower", aspect="auto", extent=[0, 2, -0.3, 1.3], cmap=cmap, norm=norm, interpolation="bilinear"
)

ax.set_facecolor("black")
fig.patch.set_facecolor("#0a0a0a")

# Style
ax.set_xlabel("Time (UI)", fontsize=20, color="white")
ax.set_ylabel("Voltage (V)", fontsize=20, color="white")
ax.set_title("eye-diagram-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="white")
ax.tick_params(axis="both", labelsize=16, colors="white")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_color("#555555")
ax.spines["left"].set_color("#555555")

ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])
ax.axhline(y=0.0, color="#444444", linewidth=0.8, linestyle="--", alpha=0.5)
ax.axhline(y=1.0, color="#444444", linewidth=0.8, linestyle="--", alpha=0.5)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
