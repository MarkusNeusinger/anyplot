#' anyplot.ai
#' shap-waterfall: SHAP Waterfall Plot for Feature Attribution
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 95/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(ragg)
library(scales)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Semantic exception (Imprint palette): SHAP explainability plots follow the
# domain convention of red = pushes prediction up, blue = pushes it down.
POSITIVE_COLOR <- "#AE3030"  # Imprint position 5 — matte red
NEGATIVE_COLOR <- "#4467A3"  # Imprint position 3 — blue

# --- Data -----------------------------------------------------------------
# Credit-scoring model: explaining one applicant's predicted default
# probability. base_value is the mean predicted probability across the
# training set; final_value is this applicant's actual prediction.
base_value  <- 0.35
final_value <- 0.275

shap_df <- tibble::tibble(
  feature = c(
    "Credit Score", "Debt-to-Income Ratio", "Late Payments (12mo)",
    "Employment Length", "Annual Income", "Loan Amount",
    "Credit Utilization", "Age", "Open Credit Accounts", "Home Ownership"
  ),
  shap_value = c(
    -0.220, 0.150, 0.110, -0.090, -0.070,
    0.060, 0.050, -0.030, -0.020, -0.015
  )
)

waterfall_df <- shap_df %>%
  arrange(desc(abs(shap_value))) %>%
  mutate(
    rank      = row_number(),
    y_pos     = n() - rank + 1,
    cum_end   = base_value + cumsum(shap_value),
    cum_start = cum_end - shap_value,
    xmin_bar  = pmin(cum_start, cum_end),
    xmax_bar  = pmax(cum_start, cum_end),
    sign      = factor(if_else(shap_value > 0, "positive", "negative"),
                        levels = c("positive", "negative")),
    label     = sprintf("%+.2f", shap_value),
    label_x   = if_else(shap_value > 0, xmax_bar + 0.006, xmin_bar - 0.006),
    label_hjust = if_else(shap_value > 0, 0, 1)
  )

connector_df <- waterfall_df %>%
  arrange(rank) %>%
  transmute(
    x        = cum_end,
    y_top    = y_pos - 0.35,
    y_bottom = lead(y_pos) + 0.35
  ) %>%
  filter(!is.na(y_bottom))

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
  geom_rect(
    data = waterfall_df,
    aes(xmin = xmin_bar, xmax = xmax_bar,
        ymin = y_pos - 0.35, ymax = y_pos + 0.35, fill = sign),
    color = PAGE_BG, linewidth = 0.4
  ) +
  geom_segment(
    data = connector_df,
    aes(x = x, xend = x, y = y_top, yend = y_bottom),
    color = INK_SOFT, linetype = "dotted", linewidth = 0.5
  ) +
  geom_vline(xintercept = base_value, color = INK_SOFT, linetype = "dashed", linewidth = 0.6) +
  geom_vline(xintercept = final_value, color = INK, linetype = "solid", linewidth = 0.8) +
  geom_label(
    data = waterfall_df,
    aes(x = label_x, y = y_pos, label = label, hjust = label_hjust),
    size = 3.2, color = INK, fill = PAGE_BG, label.size = 0,
    label.padding = unit(0.12, "lines")
  ) +
  annotate(
    "text", x = base_value, y = 10.75,
    label = paste0("Base value  E[f(x)] = ", percent(base_value, accuracy = 0.1)),
    hjust = 0.5, vjust = 0, color = INK_SOFT, size = 3.0
  ) +
  annotate(
    "text", x = final_value, y = 0.3,
    label = paste0("Prediction  f(x) = ", percent(final_value, accuracy = 0.1)),
    hjust = 0.5, vjust = 1, color = INK, size = 3.2, fontface = "bold"
  ) +
  scale_y_continuous(
    breaks = waterfall_df$y_pos,
    labels = waterfall_df$feature,
    expand = expansion(add = c(0.8, 1.3))
  ) +
  scale_x_continuous(
    labels = percent_format(accuracy = 1),
    expand = expansion(mult = c(0.08, 0.15))
  ) +
  scale_fill_manual(
    values = c(positive = POSITIVE_COLOR, negative = NEGATIVE_COLOR),
    labels = c(positive = "Increases risk", negative = "Decreases risk"),
    name   = NULL
  ) +
  labs(
    title = "shap-waterfall · r · ggplot2 · anyplot.ai",
    x     = "Predicted Default Probability",
    y     = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.x  = element_line(color = INK, linewidth = 0.15),
    axis.title.x        = element_text(color = INK, size = 10),
    axis.text.x         = element_text(color = INK_SOFT, size = 8),
    axis.text.y         = element_text(color = INK, size = 9),
    axis.ticks          = element_blank(),
    plot.title          = element_text(color = INK, size = 12),
    legend.position     = "bottom",
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.key          = element_rect(fill = PAGE_BG, color = NA)
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
