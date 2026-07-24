#' anyplot.ai
#' polar-basic: Basic Polar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-07-24

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
    "#009E73", "#C475FD", "#4467A3", "#BD8233",
    "#AE3030", "#2ABCCD", "#954477", "#99B314"
)
BRAND <- IMPRINT_PALETTE[1]

# --- Data -----------------------------------------------------------------
# Wind direction frequency at a coastal weather station, 16-point compass.
compass_directions <- c(
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
)
n_directions <- length(compass_directions)
direction_index <- seq_len(n_directions)
prevailing_index <- 11 # SW - prevailing onshore wind for this station

angular_distance <- pmin(
    abs(direction_index - prevailing_index),
    n_directions - abs(direction_index - prevailing_index)
)
base_frequency <- 14 * exp(-0.5 * (angular_distance / 2.6)^2) + 1.5
wind_frequency <- pmax(base_frequency + rnorm(n_directions, 0, 0.6), 0.3)

wind_rose <- tibble::tibble(
    direction = factor(compass_directions, levels = compass_directions),
    frequency = wind_frequency
)

# coord_polar always draws its outer boundary circle at the axis maximum,
# exactly where the default theta-axis labels sit (a ggplot2 rendering
# quirk, not a theme setting) - so compass labels are placed manually at a
# radius comfortably inside that boundary instead of via axis.text.x.
grid_max <- ceiling(max(wind_frequency) / 5) * 5
label_radius <- grid_max + 2.5
boundary_limit <- grid_max + 5
compass_labels <- tibble::tibble(
    direction = factor(compass_directions, levels = compass_directions),
    label_radius = label_radius
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(wind_rose, aes(x = direction, y = frequency)) +
    geom_col(fill = BRAND, width = 0.85, alpha = 0.9) +
    geom_text(
        data = compass_labels,
        aes(x = direction, y = label_radius, label = direction),
        inherit.aes = FALSE, color = INK, size = 3.2
    ) +
    coord_polar(theta = "x") +
    scale_y_continuous(
        limits = c(0, boundary_limit),
        breaks = seq(0, grid_max, by = 5),
        expand = c(0, 0)
    ) +
    labs(
        title = "polar-basic · r · ggplot2 · anyplot.ai",
        x = NULL,
        y = "Wind frequency (%)"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major.x = element_blank(),
        panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
        panel.grid.minor = element_blank(),
        axis.title.x = element_blank(),
        axis.title.y = element_text(color = INK, size = 10),
        axis.text.x = element_blank(),
        axis.text.y = element_text(color = INK_SOFT, size = 7),
        axis.ticks = element_blank(),
        plot.title = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 14)),
        plot.margin = margin(20, 20, 20, 20)
    )

# --- Save -------------------------------------------------------------------
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot = p,
    device = ragg::agg_png,
    width = 6,
    height = 6,
    units = "in",
    dpi = 400
)
