#' anyplot.ai
#' bar-stacked-labeled: Stacked Bar Chart with Total Labels
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 92/100 | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data -------------------------------------------------------------------
# Quarterly revenue by product category
df <- data.frame(
  quarter = rep(c("Q1", "Q2", "Q3", "Q4"), each = 3),
  product = rep(c("Electronics", "Apparel", "Home"), 4),
  revenue = c(
    450000, 320000, 280000,  # Q1
    520000, 380000, 310000,  # Q2
    580000, 420000, 350000,  # Q3
    650000, 480000, 400000   # Q4
  )
)

# Calculate totals for each quarter (for labels above bars)
df_totals <- df %>%
  group_by(quarter) %>%
  summarize(total = sum(revenue), .groups = "drop")

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = quarter, y = revenue, fill = product)) +
  geom_col(position = "stack", width = 0.6) +
  geom_text(
    data = df_totals,
    aes(x = quarter, y = total, label = paste0("$", round(total / 1e6, 1), "M")),
    vjust = -0.3,
    size = 6,
    fontface = "bold",
    color = INK,
    inherit.aes = FALSE
  ) +
  scale_fill_manual(values = IMPRINT[1:3], name = "Product") +
  labs(
    title = "bar-stacked-labeled · R · ggplot2 · anyplot.ai",
    x = "Quarter",
    y = "Revenue ($)",
    caption = "Total quarterly revenue by product category"
  ) +
  scale_y_continuous(labels = function(x) paste0("$", round(x / 1e6, 1), "M")) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title       = element_text(color = INK, size = 20, face = "bold"),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24, face = "bold", margin = margin(b = 15)),
    plot.caption     = element_text(color = INK_SOFT, size = 12, margin = margin(t = 10)),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text      = element_text(color = INK_SOFT, size = 16),
    legend.title     = element_text(color = INK, size = 18, face = "bold"),
    legend.position  = "right",
    plot.margin      = margin(20, 20, 20, 20)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
