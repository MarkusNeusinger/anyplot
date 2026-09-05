#' anyplot.ai
#' histogram-stacked: Stacked Histogram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 83/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data --------------------------------------------------------------------
# Exam scores for three cohorts sitting the same test, stacked into shared bins
df <- bind_rows(
  tibble::tibble(score = rnorm(600, mean = 68, sd = 9),  cohort = "Freshman"),
  tibble::tibble(score = rnorm(500, mean = 76, sd = 8),  cohort = "Sophomore"),
  tibble::tibble(score = rnorm(400, mean = 83, sd = 7),  cohort = "Senior")
) %>%
  mutate(score = pmin(pmax(score, 0), 100),
         cohort = factor(cohort, levels = c("Freshman", "Sophomore", "Senior")))

# --- Plot ---------------------------------------------------------------------
p <- ggplot(df, aes(x = score, fill = cohort)) +
  geom_histogram(binwidth = 4, boundary = 0, color = PAGE_BG, linewidth = 0.3) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:3]) +
  scale_x_continuous(expand = expansion(mult = c(0.01, 0.03))) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.06))) +
  labs(
    title = "Exam Scores by Cohort · histogram-stacked · r · ggplot2 · anyplot.ai",
    x = "Exam Score",
    y = "Number of Students",
    fill = "Cohort"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.y  = element_line(color = INK, linewidth = 0.3),
    axis.line           = element_line(color = INK_SOFT),
    axis.ticks          = element_blank(),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    plot.title          = element_text(color = INK, size = 12, face = "plain"),
    legend.position      = "top",
    legend.justification = "right",
    legend.background   = element_rect(fill = PAGE_BG, color = NA),
    legend.key           = element_rect(fill = PAGE_BG, color = NA),
    legend.text          = element_text(color = INK_SOFT, size = 8),
    legend.title         = element_text(color = INK, size = 10),
    plot.margin          = margin(t = 10, r = 14, b = 8, l = 8)
  )

# --- Save ---------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
