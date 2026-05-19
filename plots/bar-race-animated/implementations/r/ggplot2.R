#' anyplot.ai
#' bar-race-animated: Animated Bar Chart Race
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-05-19

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)
library(gapminder)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# Data — top 10 countries by GDP per capita at 6 key snapshots
years_snap <- c(1952, 1967, 1977, 1987, 1997, 2007)

df_snap <- gapminder::gapminder |>
  filter(year %in% years_snap) |>
  group_by(year) |>
  slice_max(gdpPercap, n = 10, with_ties = FALSE) |>
  ungroup() |>
  mutate(
    cntry_yr = paste0(country, "___", year),
    cntry_yr = reorder(cntry_yr, gdpPercap)
  )

continent_colors <- setNames(
  OKABE_ITO[1:5],
  c("Africa", "Americas", "Asia", "Europe", "Oceania")
)

# Plot — small multiples replacing animation; each facet is one time snapshot
p <- ggplot(df_snap, aes(x = cntry_yr, y = gdpPercap, fill = continent)) +
  geom_col(width = 0.8, alpha = 0.9) +
  geom_text(
    aes(label = label_dollar(scale = 1e-3, suffix = "K", accuracy = 1)(gdpPercap)),
    hjust  = -0.1,
    color  = INK_SOFT,
    size   = 4.5
  ) +
  coord_flip() +
  scale_x_discrete(labels = function(x) sub("___.*", "", x)) +
  scale_y_continuous(
    labels = label_dollar(scale = 1e-3, suffix = "K"),
    expand = expansion(mult = c(0, 0.28))
  ) +
  scale_fill_manual(values = continent_colors, name = "Continent") +
  facet_wrap(~year, scales = "free", nrow = 2) +
  labs(
    title    = "GDP per Capita Rankings · bar-race-animated · r · ggplot2 · anyplot.ai",
    subtitle = "Kuwait leads in 1952 on oil wealth; European economies — especially Norway — rise to the top by 2007",
    x        = NULL,
    y        = "GDP per Capita (USD)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_blank(),
    panel.grid.major.x = element_line(color = INK_SOFT, linewidth = 0.25),
    panel.grid.minor   = element_blank(),
    axis.title.x       = element_text(color = INK, size = 20),
    axis.title.y       = element_blank(),
    axis.text.x        = element_text(color = INK_SOFT, size = 16),
    axis.text.y        = element_text(color = INK, size = 16),
    plot.title         = element_text(color = INK, size = 24, face = "bold",
                                      margin = margin(b = 5)),
    plot.subtitle      = element_text(color = INK_SOFT, size = 18,
                                      margin = margin(b = 15)),
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                      linewidth = 0.3),
    legend.text        = element_text(color = INK_SOFT, size = 16),
    legend.title       = element_text(color = INK, size = 18),
    legend.position    = "bottom",
    strip.text         = element_text(color = INK, size = 18, face = "bold"),
    strip.background   = element_rect(fill = ELEVATED_BG, color = NA),
    plot.margin        = margin(15, 15, 10, 15)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
