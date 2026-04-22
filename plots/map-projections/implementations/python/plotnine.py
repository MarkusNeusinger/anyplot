""" pyplots.ai
map-projections: World Map with Different Projections
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    facet_wrap,
    geom_path,
    geom_polygon,
    ggplot,
    labs,
    theme,
)


# Seed for reproducibility
np.random.seed(42)

# More detailed continent boundaries (lon, lat pairs)
# North America - more realistic coastline
na_lon = np.array(
    [
        -168,
        -165,
        -155,
        -145,
        -140,
        -135,
        -130,
        -127,
        -124,
        -122,
        -120,
        -118,
        -115,
        -112,
        -108,
        -105,
        -100,
        -97,
        -95,
        -90,
        -88,
        -85,
        -82,
        -80,
        -78,
        -75,
        -72,
        -68,
        -65,
        -60,
        -55,
        -52,
        -55,
        -60,
        -65,
        -70,
        -75,
        -80,
        -85,
        -90,
        -95,
        -100,
        -105,
        -110,
        -115,
        -120,
        -130,
        -140,
        -150,
        -160,
        -168,
    ]
)
na_lat = np.array(
    [
        65,
        62,
        60,
        62,
        60,
        58,
        55,
        52,
        48,
        45,
        42,
        38,
        35,
        32,
        30,
        28,
        26,
        26,
        28,
        30,
        28,
        26,
        25,
        27,
        30,
        35,
        40,
        45,
        47,
        48,
        47,
        42,
        38,
        35,
        32,
        30,
        28,
        26,
        28,
        30,
        28,
        30,
        32,
        35,
        40,
        48,
        55,
        60,
        62,
        64,
        65,
    ]
)
continents_raw = [("North America", na_lon, na_lat)]

# South America - more realistic
sa_lon = np.array(
    [
        -82,
        -80,
        -78,
        -75,
        -72,
        -68,
        -65,
        -60,
        -55,
        -50,
        -45,
        -40,
        -35,
        -38,
        -42,
        -48,
        -52,
        -58,
        -62,
        -68,
        -72,
        -75,
        -78,
        -80,
        -82,
    ]
)
sa_lat = np.array(
    [10, 8, 5, 2, 0, -2, -5, -4, 0, 2, 0, -5, -8, -15, -22, -28, -35, -45, -55, -52, -40, -25, -15, -5, 10]
)
continents_raw.append(("South America", sa_lon, sa_lat))

# Europe - more realistic
eu_lon = np.array(
    [
        -10,
        -8,
        -5,
        0,
        5,
        8,
        12,
        15,
        18,
        22,
        25,
        28,
        32,
        35,
        40,
        45,
        50,
        55,
        60,
        65,
        60,
        55,
        50,
        45,
        40,
        35,
        30,
        25,
        20,
        15,
        10,
        5,
        0,
        -5,
        -10,
    ]
)
eu_lat = np.array(
    [
        36,
        38,
        40,
        43,
        44,
        45,
        46,
        44,
        42,
        40,
        38,
        36,
        38,
        40,
        42,
        45,
        48,
        52,
        55,
        60,
        65,
        68,
        70,
        70,
        68,
        70,
        68,
        65,
        62,
        58,
        55,
        50,
        48,
        44,
        36,
    ]
)
continents_raw.append(("Europe", eu_lon, eu_lat))

# Africa - more realistic
af_lon = np.array(
    [
        -17,
        -15,
        -12,
        -8,
        -5,
        0,
        5,
        10,
        15,
        20,
        25,
        30,
        32,
        35,
        40,
        45,
        50,
        52,
        48,
        45,
        40,
        35,
        32,
        30,
        28,
        25,
        22,
        18,
        15,
        12,
        10,
        8,
        5,
        2,
        0,
        -5,
        -10,
        -15,
        -17,
    ]
)
af_lat = np.array(
    [
        20,
        22,
        25,
        30,
        35,
        37,
        37,
        35,
        32,
        32,
        30,
        28,
        25,
        22,
        15,
        10,
        5,
        0,
        -5,
        -12,
        -18,
        -25,
        -30,
        -33,
        -35,
        -34,
        -32,
        -28,
        -25,
        -20,
        -15,
        -10,
        -5,
        5,
        10,
        15,
        18,
        20,
        20,
    ]
)
continents_raw.append(("Africa", af_lon, af_lat))

# Asia - more realistic
as_lon = np.array(
    [
        60,
        65,
        70,
        75,
        80,
        85,
        90,
        95,
        100,
        105,
        110,
        115,
        120,
        125,
        130,
        135,
        140,
        145,
        150,
        145,
        140,
        135,
        130,
        125,
        120,
        115,
        110,
        105,
        100,
        95,
        90,
        85,
        80,
        75,
        70,
        68,
        65,
        60,
        55,
        50,
        45,
        40,
        35,
        32,
        35,
        40,
        50,
        60,
    ]
)
as_lat = np.array(
    [
        40,
        45,
        50,
        55,
        60,
        65,
        68,
        70,
        72,
        75,
        72,
        70,
        68,
        65,
        60,
        55,
        52,
        48,
        45,
        42,
        38,
        35,
        32,
        28,
        25,
        22,
        18,
        12,
        8,
        10,
        15,
        18,
        20,
        22,
        25,
        28,
        30,
        32,
        35,
        38,
        38,
        40,
        38,
        35,
        32,
        32,
        35,
        40,
    ]
)
continents_raw.append(("Asia", as_lon, as_lat))

# Australia - more realistic
au_lon = np.array(
    [
        115,
        118,
        122,
        125,
        128,
        132,
        135,
        138,
        142,
        145,
        148,
        151,
        153,
        150,
        147,
        143,
        140,
        138,
        135,
        132,
        128,
        125,
        122,
        118,
        115,
    ]
)
au_lat = np.array(
    [
        -20,
        -18,
        -15,
        -14,
        -15,
        -12,
        -12,
        -14,
        -12,
        -14,
        -18,
        -22,
        -28,
        -35,
        -38,
        -38,
        -36,
        -34,
        -32,
        -30,
        -28,
        -25,
        -22,
        -20,
        -20,
    ]
)
continents_raw.append(("Australia", au_lon, au_lat))

# Antarctica - simplified band
an_lon = np.linspace(-180, 180, 40)
an_lat_north = np.array([-62 - 8 * np.abs(np.sin(np.radians(lon))) for lon in an_lon])
an_lon_full = np.concatenate([an_lon, an_lon[::-1], [an_lon[0]]])
an_lat_full = np.concatenate([an_lat_north, np.full(40, -85), [an_lat_north[0]]])
continents_raw.append(("Antarctica", an_lon_full, an_lat_full))

# Build continent dataframe
continents_list = []
for name, lons, lats in continents_raw:
    for i in range(len(lons)):
        continents_list.append({"continent": name, "order": i, "lon": lons[i], "lat": lats[i]})
df_continents = pd.DataFrame(continents_list)

# Generate graticule with high resolution for smooth curves
graticule_list = []
# Longitude lines (meridians) every 30 degrees - 200 points for smooth curves
for lon_val in range(-180, 181, 30):
    lats = np.linspace(-85, 85, 200)
    for i, lat_val in enumerate(lats):
        graticule_list.append(
            {"type": "meridian", "group": f"lon_{lon_val}", "lon": lon_val, "lat": lat_val, "order": i}
        )

# Latitude lines (parallels) every 30 degrees - 300 points for smooth curves
for lat_val in range(-60, 61, 30):
    lons = np.linspace(-180, 180, 300)
    for i, lon_val in enumerate(lons):
        graticule_list.append(
            {"type": "parallel", "group": f"lat_{lat_val}", "lon": lon_val, "lat": lat_val, "order": i}
        )

df_graticule = pd.DataFrame(graticule_list)

# Projection transformations
proj_order = ["Equirectangular", "Mercator", "Robinson", "Mollweide"]

# Equirectangular (Plate Carree)
df_equi_cont = df_continents.copy()
df_equi_cont["x"] = np.radians(df_equi_cont["lon"])
df_equi_cont["y"] = np.radians(df_equi_cont["lat"])
df_equi_cont["projection"] = "Equirectangular"

df_equi_grat = df_graticule.copy()
df_equi_grat["x"] = np.radians(df_equi_grat["lon"])
df_equi_grat["y"] = np.radians(df_equi_grat["lat"])
df_equi_grat["projection"] = "Equirectangular"

# Mercator projection
df_merc_cont = df_continents.copy()
df_merc_cont["x"] = np.radians(df_merc_cont["lon"])
lat_clipped = np.clip(df_merc_cont["lat"], -85, 85)
df_merc_cont["y"] = np.log(np.tan(np.pi / 4 + np.radians(lat_clipped) / 2))
df_merc_cont["projection"] = "Mercator"

df_merc_grat = df_graticule.copy()
df_merc_grat["x"] = np.radians(df_merc_grat["lon"])
lat_clipped_g = np.clip(df_merc_grat["lat"], -85, 85)
df_merc_grat["y"] = np.log(np.tan(np.pi / 4 + np.radians(lat_clipped_g) / 2))
df_merc_grat["projection"] = "Mercator"

# Robinson projection (lookup table)
lat_table = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90])
x_table = np.array(
    [
        1.0,
        0.9986,
        0.9954,
        0.99,
        0.9822,
        0.973,
        0.96,
        0.9427,
        0.9216,
        0.8962,
        0.8679,
        0.835,
        0.7986,
        0.7597,
        0.7186,
        0.6732,
        0.6213,
        0.5722,
        0.5322,
    ]
)
y_table = np.array(
    [
        0.0,
        0.062,
        0.124,
        0.186,
        0.248,
        0.31,
        0.372,
        0.434,
        0.4958,
        0.5571,
        0.6176,
        0.6769,
        0.7346,
        0.7903,
        0.8435,
        0.8936,
        0.9394,
        0.9761,
        1.0,
    ]
)

df_robi_cont = df_continents.copy()
abs_lat_c = np.abs(df_robi_cont["lat"])
x_factor_c = np.interp(abs_lat_c, lat_table, x_table)
y_factor_c = np.interp(abs_lat_c, lat_table, y_table)
df_robi_cont["x"] = np.radians(df_robi_cont["lon"]) * x_factor_c * 0.8487
df_robi_cont["y"] = y_factor_c * np.sign(df_robi_cont["lat"]) * 1.3523
df_robi_cont["projection"] = "Robinson"

df_robi_grat = df_graticule.copy()
abs_lat_g = np.abs(df_robi_grat["lat"])
x_factor_g = np.interp(abs_lat_g, lat_table, x_table)
y_factor_g = np.interp(abs_lat_g, lat_table, y_table)
df_robi_grat["x"] = np.radians(df_robi_grat["lon"]) * x_factor_g * 0.8487
df_robi_grat["y"] = y_factor_g * np.sign(df_robi_grat["lat"]) * 1.3523
df_robi_grat["projection"] = "Robinson"

# Mollweide projection (iterative solution)
df_moll_cont = df_continents.copy()
lon_rad_c = np.radians(df_moll_cont["lon"].values)
lat_rad_c = np.radians(df_moll_cont["lat"].values)
theta_c = lat_rad_c.copy()
for _ in range(15):
    denom = 2 + 2 * np.cos(2 * theta_c)
    denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
    theta_c = theta_c - (2 * theta_c + np.sin(2 * theta_c) - np.pi * np.sin(lat_rad_c)) / denom
df_moll_cont["x"] = 2 * np.sqrt(2) / np.pi * lon_rad_c * np.cos(theta_c)
df_moll_cont["y"] = np.sqrt(2) * np.sin(theta_c)
df_moll_cont["projection"] = "Mollweide"

df_moll_grat = df_graticule.copy()
lon_rad_g = np.radians(df_moll_grat["lon"].values)
lat_rad_g = np.radians(df_moll_grat["lat"].values)
theta_g = lat_rad_g.copy()
for _ in range(15):
    denom = 2 + 2 * np.cos(2 * theta_g)
    denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
    theta_g = theta_g - (2 * theta_g + np.sin(2 * theta_g) - np.pi * np.sin(lat_rad_g)) / denom
df_moll_grat["x"] = 2 * np.sqrt(2) / np.pi * lon_rad_g * np.cos(theta_g)
df_moll_grat["y"] = np.sqrt(2) * np.sin(theta_g)
df_moll_grat["projection"] = "Mollweide"

# Combine all projections
df_all_continents = pd.concat([df_equi_cont, df_merc_cont, df_robi_cont, df_moll_cont], ignore_index=True)
df_all_graticule = pd.concat([df_equi_grat, df_merc_grat, df_robi_grat, df_moll_grat], ignore_index=True)

# Create unique group identifiers
df_all_graticule["proj_group"] = df_all_graticule["projection"] + "_" + df_all_graticule["group"]
df_all_continents["proj_continent"] = df_all_continents["projection"] + "_" + df_all_continents["continent"]

# Set projection as ordered categorical
df_all_continents["projection"] = pd.Categorical(df_all_continents["projection"], categories=proj_order, ordered=True)
df_all_graticule["projection"] = pd.Categorical(df_all_graticule["projection"], categories=proj_order, ordered=True)

# Create the multi-panel projection comparison plot
plot = (
    ggplot()
    + geom_path(aes(x="x", y="y", group="proj_group"), data=df_all_graticule, color="#B0C4DE", size=0.4, alpha=0.6)
    + geom_polygon(
        aes(x="x", y="y", group="proj_continent"),
        data=df_all_continents,
        fill="#306998",
        color="#1a3a52",
        size=0.6,
        alpha=0.85,
    )
    + facet_wrap("~projection", ncol=2, scales="free")
    + coord_fixed(ratio=1.0)
    + labs(
        title="map-projections · plotnine · pyplots.ai",
        subtitle="Comparison of cartographic projections: Equirectangular, Mercator, Robinson, and Mollweide",
    )
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=28, weight="bold", ha="center"),
        plot_subtitle=element_text(size=18, ha="center", color="#555555"),
        strip_text=element_text(size=20, weight="bold"),
        strip_background=element_rect(fill="#f0f0f0"),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="#E8F4F8"),
        plot_background=element_rect(fill="white"),
        legend_position="none",
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
