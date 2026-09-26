#' anyplot.ai
#' bubble-basic: Basic Bubble Chart
#' Library: ggplot2 3.5.1 | R 4.4.1

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

# Data — synthetic retail catalog: price vs. customer rating, bubble = annual
# sales volume, colored by product category. Category price medians follow a
# real-world cheap-to-expensive ladder (beauty < apparel < home & kitchen <
# sports < electronics), which keeps the five categories visually separated
# along the log price axis instead of fully overlapping in one price band.
n_per_category <- 22

category_params <- tibble::tibble(
    category  = c("Electronics", "Apparel", "Home & Kitchen", "Beauty", "Sports"),
    code      = c("ELEC", "APRL", "HOME", "BEAU", "SPRT"),
    price_mu  = c(5.80, 3.47, 4.00, 2.77, 4.44),
    price_sd  = c(0.55, 0.45, 0.45, 0.45, 0.45),
    rating_mu = c(4.1, 3.9, 4.0, 4.2, 3.95),
    rating_sd = c(0.35, 0.40, 0.35, 0.30, 0.40),
    sales_mu  = c(8.5, 10.5, 9.6, 11.0, 9.8),
    sales_sd  = c(0.70, 0.60, 0.65, 0.60, 0.65)
)

products <- lapply(seq_len(nrow(category_params)), function(i) {
    p <- category_params[i, ]
    tibble::tibble(
        category     = p$category,
        price        = pmin(2500, pmax(3, rlnorm(n_per_category, meanlog = p$price_mu, sdlog = p$price_sd))),
        rating       = pmin(5, pmax(1, rnorm(n_per_category, mean = p$rating_mu, sd = p$rating_sd))),
        sales_volume = pmin(450000, pmax(300, rlnorm(n_per_category, meanlog = p$sales_mu, sdlog = p$sales_sd))),
        product_id   = sprintf("%s-%03d", p$code, seq_len(n_per_category))
    )
}) |>
    dplyr::bind_rows() |>
    dplyr::mutate(category = factor(category, levels = category_params$category))

category_colors <- stats::setNames(IMPRINT_PALETTE, levels(products$category))

# Top 3 best-sellers by annual sales volume — labeled with a short leader
# line. Direction alternates by price order (not sales-volume order) so two
# best-sellers that happen to sit close together on price don't get pushed
# to the same side and collide.
top_sellers <- products |>
    dplyr::slice_max(sales_volume, n = 3) |>
    dplyr::arrange(price) |>
    dplyr::mutate(
        direction   = rep(c(1, -1), length.out = dplyr::n()),
        label_y     = rating + direction * 0.6,
        label_vjust = ifelse(direction > 0, -0.4, 1.4)
    )

# Plot
p <- ggplot(products, aes(
    x    = price,
    y    = rating,
    size = sales_volume,
    fill = category
)) +
    geom_point(
        shape  = 21,
        color  = PAGE_BG,
        alpha  = 0.65,
        stroke = 0.4
    ) +
    geom_segment(
        data        = top_sellers,
        mapping     = aes(x = price, y = rating, xend = price, yend = label_y),
        inherit.aes = FALSE,
        color       = INK_SOFT,
        linewidth   = 0.3
    ) +
    geom_text(
        data        = top_sellers,
        mapping     = aes(x = price, y = label_y, label = product_id, vjust = label_vjust),
        inherit.aes = FALSE,
        color       = INK,
        size        = 3.2,
        fontface    = "bold"
    ) +
    scale_x_log10(
        labels = label_dollar(accuracy = 1),
        breaks = c(10, 30, 100, 300, 1000)
    ) +
    scale_y_continuous(
        limits = c(0.8, 5.7),
        breaks = 1:5
    ) +
    scale_size_area(
        max_size = 18,
        breaks   = c(5000, 50000, 150000, 400000),
        labels   = c("5K", "50K", "150K", "400K"),
        name     = "Annual Sales"
    ) +
    scale_fill_manual(values = category_colors, name = "Category") +
    labs(
        title = "bubble-basic · r · ggplot2 · anyplot.ai",
        x     = "Price ($, log scale)",
        y     = "Customer Rating (out of 5)"
    ) +
    guides(
        fill = guide_legend(override.aes = list(size = 4, alpha = 0.9))
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG,     color = NA),
        panel.grid.major  = element_line(color = GRID,       linewidth = 0.4),
        panel.grid.minor  = element_blank(),
        axis.title        = element_text(color = INK,        size = 10),
        axis.text         = element_text(color = INK_SOFT,   size = 8),
        plot.title        = element_text(color = INK,        size = 12),
        legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                         linewidth = 0.3),
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
