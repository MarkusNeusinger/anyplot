#' anyplot.ai
#' violin-box: Violin Plot with Embedded Box Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 83/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
# Resting heart rate (bpm) across three training regimens
df <- bind_rows(
  tibble::tibble(group = "Sedentary",   value = rnorm(150, mean = 74, sd = 7)),
  tibble::tibble(group = "Recreational", value = rnorm(150, mean = 65, sd = 6)),
  tibble::tibble(group = "Endurance",   value = rnorm(150, mean = 54, sd = 5))
) %>%
  mutate(group = factor(group, levels = c("Sedentary", "Recreational", "Endurance")))

title_text <- "violin-box · r · ggplot2 · anyplot.ai"

# --- Plot -----------------------------------------------------------------
p <- ggplot(df, aes(x = group, y = value, fill = group)) +
  geom_violin(color = INK_SOFT, linewidth = 0.35, width = 0.9, trim = FALSE) +
  geom_boxplot(width = 0.14, color = INK, fill = PAGE_BG,
               outlier.color = INK_SOFT, outlier.size = 3.2,
               linewidth = 0.5) +
  stat_summary(fun = mean, geom = "point", shape = 23, size = 3,
               color = INK, fill = PAGE_BG, stroke = 0.6) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  labs(
    title = title_text,
    x = "Training Regimen",
    y = "Resting Heart Rate (bpm)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.15),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12),
    legend.position   = "none"
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
