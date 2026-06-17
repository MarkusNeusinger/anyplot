#' anyplot.ai
#' star-chart-constellation: Star Chart with Constellations
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 91/100 | Created: 2026-06-17

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette — continuous magnitude scale (imprint_seq: brand green -> blue)
IMPRINT_SEQ_LOW  <- "#009E73"  # brightest stars (low magnitude) -> brand green
IMPRINT_SEQ_HIGH <- "#4467A3"  # faintest stars  (high magnitude) -> blue

# --- Data: notable stars across northern constellations ---------------------
# ra in hours (0-24), dec in degrees, mag = apparent visual magnitude
named <- tibble::tribble(
    ~star_id,       ~ra,    ~dec,    ~mag,  ~constellation,
    # Ursa Major (Big Dipper)
    "Dubhe",        11.06,  61.75,   1.79,  "Ursa Major",
    "Merak",        11.03,  56.38,   2.37,  "Ursa Major",
    "Phecda",       11.90,  53.69,   2.44,  "Ursa Major",
    "Megrez",       12.26,  57.03,   3.31,  "Ursa Major",
    "Alioth",       12.90,  55.96,   1.77,  "Ursa Major",
    "Mizar",        13.40,  54.93,   2.04,  "Ursa Major",
    "Alkaid",       13.79,  49.31,   1.86,  "Ursa Major",
    # Ursa Minor (Little Dipper)
    "Polaris",       2.53,  89.26,   1.98,  "Ursa Minor",
    "Yildun",       17.54,  86.59,   4.36,  "Ursa Minor",
    "Epsilon UMi",  16.77,  82.04,   4.21,  "Ursa Minor",
    "Zeta UMi",     15.73,  77.79,   4.32,  "Ursa Minor",
    "Eta UMi",      16.29,  75.76,   4.95,  "Ursa Minor",
    "Kochab",       14.85,  74.16,   2.08,  "Ursa Minor",
    "Pherkad",      15.35,  71.83,   3.05,  "Ursa Minor",
    # Cassiopeia (W)
    "Caph",          0.15,  59.15,   2.27,  "Cassiopeia",
    "Schedar",       0.68,  56.54,   2.24,  "Cassiopeia",
    "Gamma Cas",     0.95,  60.72,   2.47,  "Cassiopeia",
    "Ruchbah",       1.43,  60.24,   2.68,  "Cassiopeia",
    "Segin",         1.91,  63.67,   3.38,  "Cassiopeia",
    # Cygnus (Northern Cross)
    "Deneb",        20.69,  45.28,   1.25,  "Cygnus",
    "Sadr",         20.37,  40.26,   2.23,  "Cygnus",
    "Gienah Cyg",   20.77,  33.97,   2.48,  "Cygnus",
    "Delta Cyg",    19.75,  45.13,   2.87,  "Cygnus",
    "Albireo",      19.51,  27.96,   3.18,  "Cygnus",
    # Lyra
    "Vega",         18.62,  38.78,   0.03,  "Lyra",
    "Sheliak",      18.83,  33.36,   3.52,  "Lyra",
    "Sulafat",      18.98,  32.69,   3.25,  "Lyra",
    "Zeta Lyr",     18.75,  37.60,   4.36,  "Lyra",
    "Delta Lyr",    18.90,  36.90,   4.30,  "Lyra",
    # Bootes (the Kite)
    "Arcturus",     14.26,  19.18,  -0.05,  "Bootes",
    "Izar",         14.75,  27.07,   2.35,  "Bootes",
    "Seginus",      14.53,  38.31,   3.03,  "Bootes",
    "Nekkar",       15.03,  40.39,   3.49,  "Bootes",
    "Delta Boo",    15.26,  33.31,   3.47,  "Bootes",
    "Rho Boo",      14.53,  30.37,   3.58,  "Bootes",
    # Leo
    "Regulus",      10.14,  11.97,   1.36,  "Leo",
    "Eta Leo",      10.12,  16.76,   3.48,  "Leo",
    "Algieba",      10.33,  19.84,   2.08,  "Leo",
    "Adhafera",     10.28,  23.42,   3.43,  "Leo",
    "Zosma",        11.24,  20.52,   2.56,  "Leo",
    "Chort",        11.24,  15.43,   3.33,  "Leo",
    "Denebola",     11.82,  14.57,   2.14,  "Leo",
    # Gemini
    "Pollux",        7.76,  28.03,   1.14,  "Gemini",
    "Castor",        7.58,  31.89,   1.58,  "Gemini",
    "Alhena",        6.63,  16.40,   1.93,  "Gemini",
    "Mebsuta",       6.73,  25.13,   3.06,  "Gemini",
    "Tejat",         6.38,  22.51,   2.87,  "Gemini",
    # Orion
    "Betelgeuse",    5.92,   7.41,   0.42,  "Orion",
    "Bellatrix",     5.42,   6.35,   1.64,  "Orion",
    "Rigel",         5.24,  -8.20,   0.18,  "Orion",
    "Saiph",         5.80,  -9.67,   2.07,  "Orion",
    "Alnitak",       5.68,  -1.94,   1.77,  "Orion",
    "Alnilam",       5.60,  -1.20,   1.69,  "Orion",
    "Mintaka",       5.53,  -0.30,   2.23,  "Orion",
    # Auriga (+ Taurus)
    "Capella",       5.28,  46.00,   0.08,  "Auriga",
    "Menkalinan",    5.99,  44.95,   1.90,  "Auriga",
    "Mahasim",       5.99,  37.21,   2.62,  "Auriga",
    "Hassaleh",      4.95,  33.17,   2.69,  "Auriga",
    "Elnath",        5.44,  28.61,   1.65,  "Auriga",
    "Aldebaran",     4.60,  16.51,   0.87,  "Taurus"
) %>%
    mutate(is_field = FALSE)

# Faint background field stars (uniform on the sphere via sin(dec)) to give depth
n_field <- 280
field <- tibble::tibble(
    star_id       = paste0("field_", seq_len(n_field)),
    ra            = runif(n_field, 0, 24),
    dec           = asin(runif(n_field, sin(-15 * pi / 180), sin(88 * pi / 180))) * 180 / pi,
    mag           = runif(n_field, 4.0, 5.8),
    constellation = NA_character_,
    is_field      = TRUE
)

# Azimuthal-equidistant projection centred on the north celestial pole:
#   radius = 90 - dec (degrees from pole), angle = RA. Brighter -> larger point.
DEC_LIMIT  <- -15
SKY_RADIUS <- 90 - DEC_LIMIT
stars <- bind_rows(named, field) %>%
    mutate(
        ang        = ra * pi / 12,
        radius     = 90 - dec,
        x          = radius * sin(ang),
        y          = radius * cos(ang),
        point_size = scales::rescale(-mag, to = c(1.0, 7.0))
    ) %>%
    filter(radius <= SKY_RADIUS)

# Constellation stick-figure edges (pairs of star_ids)
edges <- tibble::tribble(
    ~from,          ~to,
    "Dubhe", "Merak", "Merak", "Phecda", "Phecda", "Megrez", "Megrez", "Dubhe",
    "Megrez", "Alioth", "Alioth", "Mizar", "Mizar", "Alkaid",
    "Polaris", "Yildun", "Yildun", "Epsilon UMi", "Epsilon UMi", "Zeta UMi",
    "Zeta UMi", "Eta UMi", "Eta UMi", "Kochab", "Kochab", "Pherkad", "Pherkad", "Zeta UMi",
    "Caph", "Schedar", "Schedar", "Gamma Cas", "Gamma Cas", "Ruchbah", "Ruchbah", "Segin",
    "Deneb", "Sadr", "Sadr", "Albireo", "Delta Cyg", "Sadr", "Sadr", "Gienah Cyg",
    "Vega", "Zeta Lyr", "Zeta Lyr", "Delta Lyr", "Delta Lyr", "Sulafat",
    "Sulafat", "Sheliak", "Sheliak", "Zeta Lyr",
    "Arcturus", "Izar", "Izar", "Delta Boo", "Delta Boo", "Nekkar",
    "Nekkar", "Seginus", "Seginus", "Rho Boo", "Rho Boo", "Arcturus",
    "Regulus", "Eta Leo", "Eta Leo", "Algieba", "Algieba", "Adhafera",
    "Algieba", "Zosma", "Zosma", "Denebola", "Denebola", "Chort", "Chort", "Regulus",
    "Castor", "Pollux", "Castor", "Mebsuta", "Mebsuta", "Tejat", "Pollux", "Alhena",
    "Betelgeuse", "Bellatrix", "Betelgeuse", "Alnitak", "Bellatrix", "Mintaka",
    "Alnitak", "Alnilam", "Alnilam", "Mintaka", "Alnitak", "Saiph",
    "Mintaka", "Rigel", "Saiph", "Rigel",
    "Capella", "Menkalinan", "Menkalinan", "Mahasim", "Mahasim", "Elnath",
    "Elnath", "Hassaleh", "Hassaleh", "Capella", "Elnath", "Aldebaran"
)

coords <- stars %>% select(star_id, x, y)
edge_lines <- edges %>%
    left_join(coords %>% rename(from = star_id), by = "from") %>%
    left_join(coords %>% rename(to = star_id, xend = x, yend = y), by = "to")

# Constellation name labels at the centroid of each constellation's bright stars
con_labels <- stars %>%
    filter(!is_field) %>%
    group_by(constellation) %>%
    summarise(x = mean(x), y = mean(y), .groups = "drop")

# --- Sky scaffolding: disc, declination circles, RA spokes, boundary --------
disc <- tibble::tibble(t = seq(0, 2 * pi, length.out = 240)) %>%
    mutate(x = SKY_RADIUS * cos(t), y = SKY_RADIUS * sin(t))

dec_circles <- tidyr::expand_grid(dec = c(0, 30, 60), t = seq(0, 2 * pi, length.out = 240)) %>%
    mutate(r = 90 - dec, x = r * cos(t), y = r * sin(t))

ra_spokes <- tibble::tibble(ra = seq(0, 22, by = 2)) %>%
    mutate(
        ang  = ra * pi / 12,
        xend = SKY_RADIUS * sin(ang),
        yend = SKY_RADIUS * cos(ang),
        lx   = (SKY_RADIUS + 6) * sin(ang),
        ly   = (SKY_RADIUS + 6) * cos(ang),
        lab  = paste0(ra, "h")
    )

dec_ticks <- tibble::tibble(dec = c(0, 30, 60)) %>%
    mutate(x = 4, y = 90 - dec, lab = paste0("+", dec, "°"))

# Ecliptic: the Sun's apparent annual path (obliquity 23.44 degrees)
ecliptic <- tibble::tibble(lambda = seq(0, 360, length.out = 720)) %>%
    mutate(
        lam = lambda * pi / 180,
        eps = 23.44 * pi / 180,
        dec = asin(sin(eps) * sin(lam)) * 180 / pi,
        ra  = (atan2(cos(eps) * sin(lam), cos(lam)) * 12 / pi) %% 24,
        r   = 90 - dec,
        ang = ra * pi / 12,
        # break the path (NA) where the ecliptic dips outside the sky boundary
        x   = ifelse(r <= SKY_RADIUS, r * sin(ang), NA_real_),
        y   = ifelse(r <= SKY_RADIUS, r * cos(ang), NA_real_)
    )

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
    geom_polygon(data = disc, aes(x, y), fill = ELEVATED_BG, color = NA) +
    geom_path(
        data = dec_circles, aes(x, y, group = dec),
        color = INK, alpha = 0.16, linewidth = 0.3
    ) +
    geom_segment(
        data = ra_spokes, aes(x = 0, y = 0, xend = xend, yend = yend),
        color = INK, alpha = 0.13, linewidth = 0.25
    ) +
    geom_path(
        data = ecliptic, aes(x, y),
        color = INK_MUTED, linewidth = 0.45, linetype = "dashed"
    ) +
    geom_path(data = disc, aes(x, y), color = INK_SOFT, linewidth = 0.7) +
    geom_segment(
        data = edge_lines, aes(x = x, y = y, xend = xend, yend = yend),
        color = INK_SOFT, alpha = 0.7, linewidth = 0.6
    ) +
    geom_point(
        data = stars, aes(x, y, size = point_size, color = mag)
    ) +
    geom_text(
        data = con_labels, aes(x, y, label = constellation),
        color = INK_SOFT, size = 3.4, fontface = "italic", alpha = 0.9
    ) +
    geom_text(
        data = ra_spokes, aes(lx, ly, label = lab),
        color = INK_SOFT, size = 3.0
    ) +
    geom_text(
        data = dec_ticks, aes(x, y, label = lab),
        color = INK_MUTED, size = 2.7, hjust = -0.1
    ) +
    scale_size_identity() +
    scale_color_gradient(
        low = IMPRINT_SEQ_LOW, high = IMPRINT_SEQ_HIGH,
        name = "Apparent\nmagnitude",
        guide = guide_colorbar(reverse = TRUE)
    ) +
    coord_fixed(xlim = c(-118, 118), ylim = c(-118, 118), expand = FALSE) +
    labs(title = "star-chart-constellation · r · ggplot2 · anyplot.ai") +
    theme_void(base_size = 8) +
    theme(
        plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background = element_rect(fill = PAGE_BG, color = NA),
        plot.title       = element_text(
            color = INK, size = 16, hjust = 0.5,
            margin = margin(b = 6, t = 4)
        ),
        legend.title     = element_text(color = INK, size = 11),
        legend.text      = element_text(color = INK_SOFT, size = 9),
        legend.position  = "right",
        plot.margin      = margin(14, 14, 14, 14)
    ) +
    guides(color = guide_colorbar(
        reverse = TRUE,
        barwidth = unit(0.45, "cm"),
        barheight = unit(3.4, "cm")
    ))

# --- Save -------------------------------------------------------------------
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 6,
    height   = 6,
    units    = "in",
    dpi      = 400
)
