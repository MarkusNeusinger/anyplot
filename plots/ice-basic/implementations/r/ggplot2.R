#' anyplot.ai
#' ice-basic: Individual Conditional Expectation (ICE) Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-08-17

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data -----------------------------------------------------------------
# ICE curves from a house-price model: predicted sale price as home size
# varies, one curve per house. Two age cohorts reveal a feature interaction —
# older homes plateau above a size threshold, newer homes keep climbing.
n_houses <- 100
n_grid <- 70

age_levels <- c("Newer build (<15 yr)", "Older build (15+ yr)")
house_age <- factor(
  sample(age_levels, n_houses, replace = TRUE, prob = c(0.45, 0.55)),
  levels = age_levels
)

sqft_grid <- seq(800, 3500, length.out = n_grid)

base_price      <- rnorm(n_houses, mean = 180000, sd = 22000)
price_per_sqft  <- ifelse(house_age == "Newer build (<15 yr)",
                           rnorm(n_houses, mean = 148, sd = 14),
                           rnorm(n_houses, mean = 96, sd = 18))
plateau_sqft    <- ifelse(house_age == "Older build (15+ yr)",
                           rnorm(n_houses, mean = 2200, sd = 150), Inf)
wiggle_amplitude <- rnorm(n_houses, mean = 0, sd = 9000)
wiggle_phase     <- runif(n_houses, 0, 2 * pi)

ice_df <- bind_rows(lapply(seq_len(n_houses), function(i) {
  effective_sqft <- pmin(sqft_grid, plateau_sqft[i]) +
    0.18 * pmax(sqft_grid - plateau_sqft[i], 0)
  predicted_price <- base_price[i] + price_per_sqft[i] * effective_sqft +
    wiggle_amplitude[i] * sin(sqft_grid / 650 + wiggle_phase[i])
  tibble::tibble(
    observation_id = i,
    house_age = house_age[i],
    feature_value = sqft_grid,
    prediction = predicted_price
  )
}))

pdp_df <- ice_df %>%
  group_by(feature_value) %>%
  summarize(prediction = mean(prediction), .groups = "drop")

observed_sqft <- tibble::tibble(
  feature_value = pmin(pmax(rnorm(n_houses, 1900, 480), 800), 3500)
)

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
  geom_line(
    data = ice_df,
    aes(x = feature_value, y = prediction, group = observation_id, color = house_age),
    alpha = 0.16, linewidth = 0.45
  ) +
  geom_rug(
    data = observed_sqft,
    aes(x = feature_value),
    sides = "b", color = INK_SOFT, alpha = 0.35, linewidth = 0.3
  ) +
  geom_line(
    data = pdp_df,
    aes(x = feature_value, y = prediction),
    color = INK, linewidth = 1.6
  ) +
  scale_color_manual(values = IMPRINT_PALETTE[1:2]) +
  scale_y_continuous(labels = label_dollar(scale = 1e-3, suffix = "K")) +
  guides(color = guide_legend(override.aes = list(alpha = 1, linewidth = 2))) +
  labs(
    title = "ice-basic · r · ggplot2 · anyplot.ai",
    x = "Home Size (sq ft)",
    y = "Predicted Sale Price",
    color = "House Age"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.y  = element_line(color = INK, linewidth = 0.25),
    axis.line           = element_line(color = INK_SOFT),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    plot.title          = element_text(color = INK, size = 12),
    legend.background   = element_blank(),
    legend.key          = element_blank(),
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title        = element_text(color = INK, size = 10)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
