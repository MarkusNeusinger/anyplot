"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: seaborn 0.13.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
REF_ALPHA = 0.45 if THEME == "light" else 0.65  # reference lines need more opacity on the dark page

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
P_REF = 1000  # hPa, reference pressure of the skew and of the potential temperature
P_BOTTOM, P_TOP = 1050, 45  # hPa, axis range of the diagram
T_LEFT, T_RIGHT = -55, 45  # skewed temperature axis range of the diagram
FIG_W, FIG_H = 8, 4.5  # inches, landscape canvas (3200 x 1800 px at 400 dpi)
RD, CP, LV, EPS = 287.0, 1004.0, 2.5e6, 0.622  # gas constant, heat capacity, latent heat, vapor/dry mass ratio

# Columns: set these to your table's column names
PRESSURE = "Pressure (hPa)"  # role: pressure
TEMPERATURE = "Temperature (°C)"  # role: temperature
DEWPOINT = "Dewpoint (°C)"  # role: dewpoint

# Data: replace this block with your own sounding, for example df = pd.read_csv("sounding.csv")
# Tropical atmospheric sounding: 19 levels from the surface (1000 hPa) to the stratosphere (50 hPa)
df = pd.DataFrame(
    {
        PRESSURE: [1000, 950, 925, 900, 850, 800, 750, 700, 650, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50],
        TEMPERATURE: [30, 26, 23, 21, 18, 14, 10, 6, 2, -3, -12, -22, -38, -52, -60, -65, -75, -65, -55],
        DEWPOINT: [26, 22, 18, 15, 10, 4, -2, -10, -18, -25, -38, -52, -60, -70, -75, -80, -85, -90, -90],
    }
)

# Plot: reads only df and the constants above
pressure = df[PRESSURE].to_numpy()
temperature = df[TEMPERATURE].to_numpy()
dewpoint = df[DEWPOINT].to_numpy()

# Figure with logarithmic inverted pressure axis
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=400)

ax.set_yscale("log")
ax.set_ylim(P_BOTTOM, P_TOP)
ax.set_xlim(T_LEFT, T_RIGHT)

# Pressure axis ticks and formatting
ax.yaxis.set_major_formatter(ScalarFormatter())
display_ticks = [1000, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50]
ax.set_yticks(display_ticks)
ax.set_yticklabels([str(p) for p in display_ticks])
ax.yaxis.set_minor_locator(plt.NullLocator())

# Labels and title
ax.set_xlabel(TEMPERATURE, fontsize=10, color=INK)
ax.set_ylabel(PRESSURE, fontsize=10, color=INK)
ax.set_title("skewt-logp-atmospheric · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

sns.despine(ax=ax, top=True, right=True)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.5, color=INK)

# Lay out the axes first, then derive the skew so that isotherms rise at 45 degrees on screen:
# one unit of ln(p) spans the same screen distance as SKEW degrees along the temperature axis
plt.tight_layout()
box = ax.get_position()
axes_w, axes_h = box.width * FIG_W, box.height * FIG_H
SKEW = (T_RIGHT - T_LEFT) * axes_h / (np.log(P_BOTTOM / P_TOP) * axes_w)  # degC per unit ln(p)

p_bg = np.logspace(np.log10(P_TOP), np.log10(P_BOTTOM), 150)


def skewed(t, p):
    """Plot x position of temperature t (degC) at pressure p (hPa)."""
    return t + SKEW * np.log(P_REF / p)


def draw_family(frames, key, **style):
    """Draw one reference-line family with a single seaborn lineplot call."""
    sns.lineplot(
        data=pd.concat(frames, ignore_index=True),
        x="x",
        y="pressure",
        units=key,
        estimator=None,
        sort=False,
        ax=ax,
        zorder=1,
        legend=False,
        **style,
    )


# Isotherms
iso_frames = [pd.DataFrame({"x": skewed(t, p_bg), "pressure": p_bg, "T": t}) for t in np.arange(-130, 60, 10)]
draw_family(iso_frames, "T", color=INK_SOFT, linewidth=0.5, alpha=REF_ALPHA * 0.8)

# Dry adiabats (potential temperature theta = const)
dry_frames = []
for theta in np.arange(230, 470, 20):
    t_dry = theta * (p_bg / P_REF) ** 0.286 - 273.15
    dry_frames.append(pd.DataFrame({"x": skewed(t_dry, p_bg), "pressure": p_bg, "theta": theta}))
draw_family(dry_frames, "theta", color=IMPRINT[4], linewidth=0.6, alpha=REF_ALPHA)

# Moist (pseudo-)adiabats: integrate the saturated lapse rate dT/dln(p) upward from 1000 hPa
p_up = np.logspace(np.log10(P_REF), np.log10(P_TOP), 200)
moist_frames = []
for t_start in np.arange(-10, 40, 5):
    t_k = np.empty_like(p_up)
    t_k[0] = t_start + 273.15
    for i in range(1, len(p_up)):
        t_now, p_now = t_k[i - 1], p_up[i - 1]
        e_sat = 6.112 * np.exp(17.67 * (t_now - 273.15) / (t_now - 273.15 + 243.5))
        r_sat = EPS * e_sat / (p_now - e_sat)
        dt_dlnp = (RD * t_now + LV * r_sat) / (CP + LV**2 * r_sat * EPS / (RD * t_now**2))
        t_k[i] = t_now + dt_dlnp * np.log(p_up[i] / p_now)
    moist_frames.append(pd.DataFrame({"x": skewed(t_k - 273.15, p_up), "pressure": p_up, "t_start": t_start}))
draw_family(moist_frames, "t_start", color=IMPRINT[2], linewidth=0.6, alpha=REF_ALPHA, linestyle="--")

# Mixing ratio lines (w = const, g/kg): dewpoint of the vapor pressure that w implies at each level
p_mix = np.logspace(np.log10(400), np.log10(P_BOTTOM), 60)
mix_frames = []
for w in [1, 2, 4, 7, 10, 16, 24]:
    e_w = (w / 1000) * p_mix / (EPS + w / 1000)
    t_mix = 243.5 * np.log(e_w / 6.112) / (17.67 - np.log(e_w / 6.112))
    mix_frames.append(pd.DataFrame({"x": skewed(t_mix, p_mix), "pressure": p_mix, "w": w}))
draw_family(mix_frames, "w", color=IMPRINT[3], linewidth=0.7, alpha=REF_ALPHA, linestyle=":")

# Apply skew transform to sounding data
x_temp = skewed(temperature, pressure)
x_dew = skewed(dewpoint, pressure)

# Dewpoint depression: shade the gap between temperature and dewpoint (dry air where wide, saturated where closed)
ax.fill_betweenx(pressure, x_dew, x_temp, alpha=0.14, color=IMPRINT[4], zorder=2)

df_prof = pd.DataFrame(
    {
        "x": np.concatenate([x_temp, x_dew]),
        "pressure": np.concatenate([pressure, pressure]),
        "profile": ["Temperature"] * len(pressure) + ["Dewpoint"] * len(pressure),
    }
)

# Plot sounding profiles with seaborn lineplot (hue + style + markers = seaborn-idiomatic)
sns.lineplot(
    data=df_prof,
    x="x",
    y="pressure",
    hue="profile",
    style="profile",
    markers={"Temperature": "o", "Dewpoint": "s"},
    dashes={"Temperature": "", "Dewpoint": (5, 2)},
    palette={"Temperature": IMPRINT[0], "Dewpoint": IMPRINT[1]},
    linewidth=3,
    markersize=6,
    sort=False,
    ax=ax,
    zorder=5,
    legend=False,
)

# Legend — upper-right, where the sounding leaves the diagram empty
legend_handles = [
    Line2D([0], [0], color=IMPRINT[0], lw=2.5, marker="o", markersize=5, label="Temperature"),
    Line2D([0], [0], color=IMPRINT[1], lw=2.5, linestyle=(0, (5, 2)), marker="s", markersize=5, label="Dewpoint"),
    Patch(facecolor=IMPRINT[4], alpha=0.30, edgecolor="none", label="Dewpoint depression"),
    Line2D([0], [0], color=INK_SOFT, lw=0.8, alpha=0.8, label="Isotherms"),
    Line2D([0], [0], color=IMPRINT[4], lw=0.8, alpha=0.9, label="Dry adiabats"),
    Line2D([0], [0], color=IMPRINT[2], lw=0.8, alpha=0.9, linestyle="--", label="Moist adiabats"),
    Line2D([0], [0], color=IMPRINT[3], lw=0.8, alpha=0.9, linestyle=":", label="Mixing ratio"),
]
ax.legend(
    handles=legend_handles, loc="upper right", fontsize=8, framealpha=0.92, facecolor=ELEVATED_BG, edgecolor=INK_SOFT
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
