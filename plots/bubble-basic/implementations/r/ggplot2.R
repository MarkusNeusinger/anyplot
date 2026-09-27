#' anyplot.ai
#' bubble-basic: Basic Bubble Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Updated: 2026-09-27

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- if (THEME == "light") "#D3D1CA" else "#3A3A37"

IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# Data — synthetic city-infrastructure scenario: population density vs. median
# household income, bubble = green space per capita, colored by neighborhood
# zone type. Density falls off from the urban core outward while green space
# per capita rises, which keeps the five zone types visually separated along
# the log density axis instead of overlapping in one band.
n_per_category <- 22

zone_params <- tibble::tibble(
    category   = c("Urban Core", "Inner Ring", "Outer Ring", "Industrial District", "Suburban Fringe"),
    code       = c("URBN", "INNR", "OUTR", "INDU", "SUBF"),
    density_mu = log(c(18000, 9000, 4200, 3200, 1200)),
    density_sd = c(0.35, 0.35, 0.40, 0.40, 0.45),
    income_mu  = c(58, 64, 82, 46, 98),
    income_sd  = c(9, 10, 13, 8, 14),
    green_mu   = log(c(4, 8, 18, 5, 35)),
    green_sd   = c(0.40, 0.40, 0.45, 0.35, 0.40)
)

# Flat, vectorized generation: repeat each zone's params n_per_category times,
# then draw all rows in one rlnorm()/rnorm() call each (both accept vectorized
# mean/sd arguments) instead of looping per zone.
row_params <- zone_params[rep(seq_len(nrow(zone_params)), each = n_per_category), ]
n_total <- nrow(row_params)

neighborhoods <- tibble::tibble(
    category        = row_params$category,
    density         = pmin(35000, pmax(150, rlnorm(n_total, meanlog = row_params$density_mu, sdlog = row_params$density_sd))),
    income          = pmin(180, pmax(15, rnorm(n_total, mean = row_params$income_mu, sd = row_params$income_sd))),
    green_space     = pmin(150, pmax(1, rlnorm(n_total, meanlog = row_params$green_mu, sdlog = row_params$green_sd))),
    neighborhood_id = sprintf("%s-%03d", row_params$code, rep(seq_len(n_per_category), times = nrow(zone_params)))
) |>
    dplyr::mutate(category = factor(category, levels = zone_params$category)) |>
    # Draw largest bubbles first (bottom layer) so smaller bubbles stay
    # visible on top instead of being buried in the dense low-density cluster.
    dplyr::arrange(dplyr::desc(green_space))

category_colors <- stats::setNames(IMPRINT_PALETTE, levels(neighborhoods$category))

# Bubble-size domain floor: anchoring scale_size_area() at an absolute zero
# buries the smallest real values at a couple of visible pixels. Flooring the
# lower limit just below the observed minimum keeps sizing strictly area-true
# across the data range while giving the smallest bubbles real presence.
green_range <- range(neighborhoods$green_space)
size_limits <- c(green_range[1] * 0.75, green_range[2])

# Top 3 neighborhoods by green space per capita — labeled with a short leader
# line. Direction alternates by density order (not green-space order) so two
# standouts that happen to sit close together on density don't get pushed to
# the same side and collide.
top_green <- neighborhoods |>
    dplyr::slice_max(green_space, n = 3) |>
    dplyr::arrange(density) |>
    dplyr::mutate(
        direction   = rep(c(1, -1), length.out = dplyr::n()),
        label_y     = income + direction * 16,
        label_vjust = ifelse(direction > 0, -0.4, 1.4)
    )

# Plot
p <- ggplot(neighborhoods, aes(
    x    = density,
    y    = income,
    size = green_space,
    fill = category
)) +
    geom_point(
        shape  = 21,
        color  = PAGE_BG,
        alpha  = 0.58,
        stroke = 1.0
    ) +
    geom_segment(
        data        = top_green,
        mapping     = aes(x = density, y = income, xend = density, yend = label_y),
        inherit.aes = FALSE,
        color       = INK_SOFT,
        linewidth   = 0.3
    ) +
    geom_text(
        data        = top_green,
        mapping     = aes(x = density, y = label_y, label = neighborhood_id, vjust = label_vjust),
        inherit.aes = FALSE,
        color       = INK,
        size        = 3.2,
        fontface    = "bold"
    ) +
    scale_x_log10(
        labels = label_comma(),
        breaks = c(300, 1000, 3000, 10000, 30000)
    ) +
    annotation_logticks(sides = "b", color = INK_SOFT, linewidth = 0.25) +
    scale_y_continuous(
        limits = c(15, 150),
        breaks = c(20, 50, 80, 110, 140)
    ) +
    scale_size_area(
        max_size = 18,
        limits   = size_limits,
        breaks   = c(3, 10, 25, 60, 120),
        labels   = c("3", "10", "25", "60", "120"),
        name     = "Green Space (m²/capita)"
    ) +
    scale_fill_manual(values = category_colors, name = "Zone Type") +
    labs(
        title    = "bubble-basic · r · ggplot2 · anyplot.ai",
        subtitle = "Bubble size encodes green space per capita",
        x        = "Population Density (people/km², log scale)",
        y        = "Median Household Income ($K)"
    ) +
    guides(
        fill = guide_legend(override.aes = list(size = 4, alpha = 0.9))
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG,     color = NA),
        panel.grid.major.x = element_blank(),
        panel.grid.major.y = element_line(color = GRID,      linewidth = 0.25),
        panel.grid.minor  = element_blank(),
        axis.title        = element_text(color = INK,        size = 10),
        axis.text         = element_text(color = INK_SOFT,   size = 8),
        plot.title        = element_text(color = INK,        size = 12),
        plot.subtitle     = element_text(color = INK_SOFT,   size = 9, margin = margin(b = 8)),
        legend.background = element_rect(fill = ELEVATED_BG, color = NA),
        legend.text       = element_text(color = INK_SOFT,   size = 8),
        legend.title      = element_text(color = INK,        size = 10),
        legend.key        = element_rect(fill = NA,          color = NA),
        legend.margin     = margin(6, 8, 6, 8),
        plot.margin       = margin(12, 12, 10, 10)
    )

# Save
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
