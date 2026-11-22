""" anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN = "#C8DDF0" if THEME == "light" else "#1E3050"
LAND = "#E5E5E0" if THEME == "light" else "#3A3A34"
LAND_EDGE = "#888888" if THEME == "light" else "#555550"
GRATICULE = "#AAAAAA" if THEME == "light" else "#555550"
BUBBLE_COLOR = "#009E73"  # Imprint palette position 1

# Constants
MIN_SIZE = 20  # smallest bubble area (pt^2)
MAX_SIZE = 225  # largest bubble area (pt^2)

LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
GDP = "Metro GDP (billion USD)"  # role: value
CITY = "City"  # role: label

# Data - Major world cities with GDP (in billion USD) as primary value for bubble size
np.random.seed(42)

cities = {
    "Tokyo": (35.6762, 139.6503, 1920),
    "New York": (40.7128, -74.0060, 1775),
    "Los Angeles": (34.0522, -118.2437, 1050),
    "London": (51.5074, -0.1278, 980),
    "Paris": (48.8566, 2.3522, 815),
    "Shanghai": (31.2304, 121.4737, 810),
    "Beijing": (39.9042, 116.4074, 750),
    "Seoul": (37.5665, 126.9780, 710),
    "Chicago": (41.8781, -87.6298, 680),
    "Osaka": (34.6937, 135.5023, 650),
    "Mumbai": (19.0760, 72.8777, 400),
    "São Paulo": (-23.5505, -46.6333, 430),
    "Moscow": (55.7558, 37.6173, 520),
    "Sydney": (-33.8688, 151.2093, 390),
    "Hong Kong": (22.3193, 114.1694, 380),
    "Singapore": (1.3521, 103.8198, 360),
    "Toronto": (43.6532, -79.3832, 340),
    "Mexico City": (19.4326, -99.1332, 310),
    "Bangkok": (13.7563, 100.5018, 270),
    "Jakarta": (-6.2088, 106.8456, 260),
    "Istanbul": (41.0082, 28.9784, 250),
    "Buenos Aires": (-34.6037, -58.3816, 240),
    "Dubai": (25.2048, 55.2708, 230),
    "Delhi": (28.6139, 77.2090, 220),
    "Frankfurt": (50.1109, 8.6821, 210),
}

df = pd.DataFrame(
    [(name, lat, lon, value) for name, (lat, lon, value) in cities.items()], columns=[CITY, LATITUDE, LONGITUDE, GDP]
)


# Simplified world map coastlines
continents = [
    # Alaska
    [(-168, 66), (-165, 60), (-141, 60), (-141, 70), (-156, 71), (-168, 66)],
    # North America main
    [
        (-168, 52),
        (-162, 55),
        (-152, 60),
        (-141, 60),
        (-130, 56),
        (-125, 50),
        (-124, 42),
        (-117, 33),
        (-110, 32),
        (-105, 29),
        (-97, 26),
        (-97, 28),
        (-95, 30),
        (-90, 30),
        (-85, 30),
        (-82, 25),
        (-81, 25),
        (-80, 32),
        (-75, 35),
        (-70, 41),
        (-67, 45),
        (-65, 45),
        (-64, 47),
        (-67, 48),
        (-70, 47),
        (-75, 45),
        (-80, 45),
        (-84, 46),
        (-88, 48),
        (-95, 49),
        (-102, 49),
        (-120, 49),
        (-123, 49),
        (-130, 55),
        (-140, 60),
        (-148, 60),
        (-153, 58),
        (-162, 55),
        (-168, 52),
    ],
    # Mexico + Central America
    [
        (-117, 33),
        (-115, 30),
        (-112, 29),
        (-110, 25),
        (-105, 22),
        (-100, 20),
        (-97, 20),
        (-95, 18),
        (-92, 16),
        (-88, 18),
        (-87, 16),
        (-84, 10),
        (-82, 9),
        (-78, 9),
        (-77, 8),
        (-80, 8),
        (-80, 15),
        (-88, 21),
        (-90, 22),
        (-97, 26),
        (-105, 29),
        (-110, 32),
        (-117, 33),
    ],
    # South America
    [
        (-78, 10),
        (-71, 12),
        (-67, 11),
        (-63, 10),
        (-60, 8),
        (-55, 5),
        (-50, 0),
        (-45, -2),
        (-40, -3),
        (-35, -6),
        (-35, -10),
        (-37, -15),
        (-40, -20),
        (-42, -23),
        (-47, -25),
        (-50, -28),
        (-53, -33),
        (-58, -38),
        (-66, -55),
        (-74, -52),
        (-76, -48),
        (-75, -42),
        (-72, -37),
        (-72, -30),
        (-71, -20),
        (-70, -18),
        (-78, -6),
        (-81, -3),
        (-80, 0),
        (-78, 3),
        (-77, 7),
        (-78, 10),
    ],
    # Iberian Peninsula
    [(-10, 36), (-6, 37), (-2, 36), (3, 43), (0, 44), (-2, 43), (-8, 44), (-9, 42), (-10, 36)],
    # UK
    [(-6, 50), (-5, 54), (-4, 58), (-8, 58), (-6, 55), (-6, 50)],
    # European mainland
    [
        (-5, 43),
        (0, 43),
        (3, 43),
        (6, 44),
        (8, 44),
        (12, 46),
        (14, 45),
        (14, 41),
        (16, 40),
        (20, 40),
        (24, 37),
        (26, 38),
        (28, 41),
        (30, 42),
        (32, 42),
        (34, 42),
        (37, 45),
        (40, 46),
        (44, 42),
        (50, 37),
        (52, 30),
        (56, 27),
        (60, 25),
        (70, 25),
        (75, 25),
        (78, 22),
        (78, 8),
        (76, 8),
        (72, 18),
        (70, 22),
        (66, 25),
        (60, 25),
        (56, 27),
        (50, 30),
        (42, 31),
        (37, 32),
        (33, 30),
        (30, 31),
        (25, 35),
        (22, 36),
        (18, 40),
        (14, 41),
        (12, 44),
        (10, 47),
        (8, 48),
        (5, 49),
        (4, 51),
        (3, 51),
        (5, 54),
        (10, 54),
        (10, 56),
        (12, 56),
        (14, 54),
        (19, 55),
        (22, 56),
        (24, 55),
        (28, 56),
        (30, 60),
        (32, 65),
        (28, 70),
        (20, 70),
        (12, 65),
        (10, 62),
        (5, 58),
        (3, 54),
        (-2, 50),
        (-5, 48),
        (-5, 43),
    ],
    # Africa
    [
        (-17, 14),
        (-17, 21),
        (-13, 28),
        (-10, 32),
        (-6, 35),
        (0, 36),
        (10, 37),
        (11, 34),
        (15, 32),
        (20, 32),
        (25, 32),
        (30, 31),
        (33, 30),
        (35, 28),
        (37, 22),
        (42, 14),
        (44, 11),
        (51, 11),
        (51, 3),
        (42, 0),
        (42, -4),
        (40, -10),
        (38, -18),
        (35, -22),
        (32, -28),
        (28, -33),
        (20, -35),
        (17, -30),
        (15, -25),
        (12, -17),
        (12, -6),
        (9, 4),
        (5, 5),
        (0, 6),
        (-5, 5),
        (-10, 7),
        (-15, 11),
        (-17, 14),
    ],
    # Asia main
    [
        (28, 70),
        (40, 70),
        (50, 68),
        (60, 70),
        (80, 72),
        (100, 77),
        (120, 75),
        (140, 72),
        (160, 65),
        (170, 60),
        (165, 55),
        (160, 52),
        (150, 46),
        (140, 44),
        (135, 35),
        (129, 33),
        (125, 35),
        (120, 32),
        (122, 25),
        (118, 23),
        (110, 18),
        (105, 16),
        (100, 14),
        (100, 20),
        (105, 22),
        (108, 22),
        (100, 10),
        (104, 2),
        (98, 0),
        (96, 6),
        (92, 22),
        (88, 22),
        (92, 22),
        (88, 26),
        (82, 28),
        (80, 28),
        (78, 33),
        (74, 35),
        (72, 25),
        (66, 25),
        (60, 25),
        (56, 27),
        (52, 30),
        (50, 37),
        (44, 42),
        (40, 46),
        (37, 45),
        (34, 42),
        (32, 42),
        (30, 42),
        (28, 56),
        (28, 70),
    ],
    # Japan
    [
        (130, 32),
        (132, 34),
        (136, 35),
        (140, 36),
        (141, 40),
        (141, 45),
        (145, 44),
        (145, 42),
        (144, 38),
        (140, 36),
        (136, 35),
        (132, 32),
        (130, 32),
    ],
    # Australia
    [
        (113, -22),
        (115, -21),
        (117, -20),
        (122, -18),
        (130, -12),
        (135, -12),
        (137, -16),
        (139, -17),
        (141, -13),
        (145, -15),
        (150, -23),
        (153, -28),
        (152, -33),
        (150, -37),
        (145, -38),
        (140, -38),
        (136, -35),
        (130, -32),
        (125, -32),
        (117, -35),
        (115, -34),
        (115, -30),
        (113, -25),
        (113, -22),
    ],
]

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(OCEAN)

# Draw continents
for continent in continents:
    poly = plt.Polygon(continent, facecolor=LAND, edgecolor=LAND_EDGE, linewidth=0.3, zorder=1)
    ax.add_patch(poly)

# Add graticule
for lat in range(-60, 90, 30):
    ax.axhline(y=lat, color=GRATICULE, linewidth=0.2, linestyle=":", alpha=0.6, zorder=0)
for lon in range(-150, 181, 30):
    ax.axvline(x=lon, color=GRATICULE, linewidth=0.2, linestyle=":", alpha=0.6, zorder=0)

# Bubble area scales linearly with GDP, between MIN_SIZE and MAX_SIZE
gdp_min = df[GDP].min()
gdp_span = df[GDP].max() - gdp_min
sizes = MIN_SIZE + (df[GDP] - gdp_min) / gdp_span * (MAX_SIZE - MIN_SIZE)

# Bubbles - Imprint palette position 1, edge matching the page background
ax.scatter(df[LONGITUDE], df[LATITUDE], s=sizes, c=BUBBLE_COLOR, alpha=0.6, edgecolors=PAGE_BG, linewidths=1, zorder=5)

ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10, color=INK)
ax.set_ylabel(LATITUDE, fontsize=10, color=INK)
ax.set_title(
    "City GDP by Location · bubble-map-geographic · python · matplotlib · anyplot.ai",
    fontsize=10,
    fontweight="medium",
    color=INK,
    pad=8,
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

# Size legend - reference bubbles drawn with the same scaling as the data
legend_values = [250, 750, 1500]
legend_sizes = MIN_SIZE + (np.array(legend_values) - gdp_min) / gdp_span * (MAX_SIZE - MIN_SIZE)
size_labels = ["$250B", "$750B", "$1.5T"]

size_handles = [
    ax.scatter([], [], s=sz, c=BUBBLE_COLOR, alpha=0.6, edgecolors=PAGE_BG, linewidths=0.75, label=label)
    for sz, label in zip(legend_sizes, size_labels, strict=True)
]

leg = ax.legend(
    handles=size_handles,
    title="Metro GDP",
    loc="lower left",
    fontsize=8,
    title_fontsize=8,
    fancybox=True,
    labelspacing=1.0,
    borderpad=0.9,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_alpha(0.95)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

# Save
fig.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
