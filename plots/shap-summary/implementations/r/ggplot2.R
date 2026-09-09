#' anyplot.ai
#' shap-summary: SHAP Summary Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(tibble)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
MIDPOINT_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"

# Imprint palette-derived diverging cmap (low=blue, mid=neutral, high=matte-red)
# chosen over imprint_seq because low/high feature values are the domain's
# universally recognised polarity (cold->hot / low->high), mirrored here for
# SHAP's own "low feature value -> blue, high -> red" reading convention.
SHAP_LOW  <- "#4467A3"
SHAP_HIGH <- "#AE3030"

# --- Data --------------------------------------------------------------------
# Simulated SHAP values from a gradient-boosted house-price model. Each row is
# one (sample, feature) pair: the feature's contribution to that sample's
# predicted price, plus the feature's own value (min-max normalised for color).
n_samples <- 220

make_feature <- function(name, raw, amplitude, noise_sd, shape = c("increasing", "decreasing", "hump")) {
  shape <- match.arg(shape)
  value_norm <- (raw - min(raw)) / (max(raw) - min(raw))
  trend <- switch(shape,
    increasing = (value_norm - 0.5) * 2,
    decreasing = (0.5 - value_norm) * 2,
    hump       = (1 - 4 * (value_norm - 0.5)^2 - 0.5) * 2
  )
  tibble(
    feature          = name,
    shap_value       = amplitude * trend + rnorm(n_samples, 0, noise_sd),
    feature_value    = raw,
    feature_value_norm = value_norm
  )
}

shap_df <- bind_rows(
  make_feature("Living Area (sqft)", rnorm(n_samples, 1900, 650) |> pmax(420),
               amplitude = 42000, noise_sd = 7000, shape = "increasing"),
  make_feature("Distance to Downtown (km)", runif(n_samples, 1, 25),
               amplitude = 16000, noise_sd = 5000, shape = "hump"),
  make_feature("School Rating (1-10)", runif(n_samples, 1, 10),
               amplitude = 13000, noise_sd = 4500, shape = "increasing"),
  make_feature("House Age (years)", rnorm(n_samples, 25, 15) |> pmax(0),
               amplitude = 10000, noise_sd = 4000, shape = "decreasing"),
  make_feature("Bathrooms", rpois(n_samples, 2) + 1,
               amplitude = 7000, noise_sd = 3000, shape = "increasing"),
  make_feature("Crime Rate Index", runif(n_samples, 0, 100),
               amplitude = 5500, noise_sd = 2500, shape = "decreasing"),
  make_feature("Lot Size (sqft)", rnorm(n_samples, 8000, 3000) |> pmax(1500),
               amplitude = 4000, noise_sd = 2200, shape = "increasing"),
  make_feature("Has Garage", rbinom(n_samples, 1, 0.65),
               amplitude = 3000, noise_sd = 1800, shape = "increasing")
)

# Order features by mean |SHAP value| — most important at top
importance <- shap_df |>
  group_by(feature) |>
  summarise(mean_abs_shap = mean(abs(shap_value)), .groups = "drop")

shap_df <- shap_df |>
  left_join(importance, by = "feature") |>
  mutate(feature = factor(feature, levels = importance$feature[order(importance$mean_abs_shap)]))

# Call out the top driver feature (highest mean |SHAP value|) with a star
# prefix on its axis label — a light storytelling touch beyond the raw sort.
top_feature <- importance$feature[which.max(importance$mean_abs_shap)]
feature_levels <- levels(shap_df$feature)
axis_labels <- feature_levels
axis_labels[feature_levels == top_feature] <- paste0("★ ", top_feature)

# --- Plot ----------------------------------------------------------------
# shape=21 gives points a stroke independent of fill, so mid-range values
# (fill == PAGE_BG at the diverging midpoint, per style guide) stay visible
# as a faint outlined ring rather than vanishing into the background.
p <- ggplot(shap_df, aes(x = shap_value, y = feature, fill = feature_value_norm)) +
  geom_vline(xintercept = 0, color = INK_SOFT, linewidth = 0.5, linetype = "dashed") +
  geom_jitter(shape = 21, color = INK_SOFT, stroke = 0.25,
              height = 0.30, width = 0, size = 1.9, alpha = 0.55) +
  scale_fill_gradient2(
    low = SHAP_LOW, mid = MIDPOINT_BG, high = SHAP_HIGH, midpoint = 0.5,
    breaks = c(0.06, 0.94), labels = c("Low", "High"),
    name = "Feature value",
    guide = guide_colorbar(barheight = unit(3.4, "cm"), barwidth = unit(0.35, "cm"))
  ) +
  scale_x_continuous(labels = label_dollar(scale = 1e-3, suffix = "k")) +
  scale_y_discrete(labels = axis_labels) +
  labs(
    x = "SHAP Value (Impact on Predicted Price)",
    y = NULL,
    title = "shap-summary · r · ggplot2 · anyplot.ai"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background     = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y   = element_line(color = scales::alpha(INK, 0.18), linewidth = 0.6),
    panel.grid.major.x   = element_blank(),
    panel.grid.minor      = element_blank(),
    axis.title            = element_text(color = INK, size = 10),
    axis.text             = element_text(color = INK_SOFT, size = 8),
    axis.text.y           = element_text(color = INK, size = 9),
    axis.ticks            = element_blank(),
    plot.title            = element_text(color = INK, size = 12),
    legend.background     = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text           = element_text(color = INK_SOFT, size = 8),
    legend.title          = element_text(color = INK, size = 10),
    legend.position        = "right",
    plot.margin            = margin(t = 10, r = 12, b = 8, l = 8)
  )

# --- Save --------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
