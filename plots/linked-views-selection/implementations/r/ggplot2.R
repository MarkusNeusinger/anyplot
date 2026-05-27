#' anyplot.ai
#' linked-views-selection: Multiple Linked Views with Selection Sync
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 81/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- if (THEME == "light") "#D4D4D0" else "#3A3A36"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data -------------------------------------------------------------------
# Create coordinated dataset: multivariate iris with clear groupings
df <- iris %>%
  mutate(
    id = row_number(),
    view = "Data",
    size_group = case_when(
      Sepal.Length < 5.5 ~ "Compact",
      Sepal.Length < 6.5 ~ "Standard",
      TRUE ~ "Large"
    )
  )

# --- Theme settings ----------------------------------------------------------
anyplot_theme <- theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID, linewidth = 0.2),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title        = element_text(color = INK, size = 20, face = "plain"),
    axis.text         = element_text(color = INK_SOFT, size = 16),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 28, face = "plain", margin = margin(b = 20)),
    strip.text        = element_text(color = INK, size = 16, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.5),
    legend.text       = element_text(color = INK_SOFT, size = 16),
    legend.title      = element_text(color = INK, size = 18, face = "bold"),
    legend.position   = "bottom",
    strip.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.5),
    plot.margin       = margin(20, 20, 20, 20)
  )

# --- Create coordinated views as faceted scatter plots ---------------------
# Three perspectives on the same data with consistent coloring
df_views <- rbind(
  df %>% mutate(
    x_val = Sepal.Length,
    y_val = Sepal.Width,
    view_name = "Sepal Length vs Width (cm)"
  ),
  df %>% mutate(
    x_val = Sepal.Length,
    y_val = Petal.Length,
    view_name = "Sepal vs Petal Length (cm)"
  ),
  df %>% mutate(
    x_val = Petal.Length,
    y_val = Petal.Width,
    view_name = "Petal Length vs Width (cm)"
  )
)

# --- Main plot: Multiple linked views ----------------------------------------
p <- ggplot(df_views, aes(x = x_val, y = y_val, color = Species)) +
  geom_point(size = 5, alpha = 0.75) +
  scale_color_manual(values = IMPRINT[1:3]) +
  facet_wrap(~view_name, scales = "free", ncol = 3) +
  labs(
    title = "linked-views-selection · ggplot2 · anyplot.ai",
    x = "Measurement (cm)",
    y = "Measurement (cm)",
    color = "Species"
  ) +
  anyplot_theme

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
