# anyplot.ai
# sparkline-basic: Basic Sparkline
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 82/100 | Created: 2026-09-09

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
# Daily active users for a SaaS product over a quarter, mild upward drift
n = 60
day = 1:n
daily_steps = randn(n - 1) .* 140 .+ 6
daily_active_users = 11_800.0 .+ cumsum(vcat(0.0, daily_steps))

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "sparkline-basic · julia · makie · anyplot.ai"

ax = Axis(
    fig[1, 1];
    title           = title_str,
    titlesize       = 26,
    titlecolor      = INK,
    titlegap        = 36,
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)

y_min, y_max = extrema(daily_active_users)
y_range = y_max - y_min
y_pad = y_range * 1.0
ylims!(ax, y_min - y_pad, y_max + y_pad)
xlims!(ax, day[1] - 0.5, day[end] + 0.5)

idx_min = argmin(daily_active_users)
idx_max = argmax(daily_active_users)

# True area-fill effect: shade down to the series' own minimum, not the padded canvas.
band!(ax, day, fill(y_min, n), daily_active_users; color = (BRAND, 0.22))
lines!(ax, day, daily_active_users; color = BRAND, linewidth = 3.5)

# Optional sparkline conventions: min/max highlights + first/last reference points.
scatter!(
    ax, [day[idx_min]], [daily_active_users[idx_min]];
    color = IMPRINT_PALETTE[3], markersize = 16, strokewidth = 0,
)
scatter!(
    ax, [day[idx_max]], [daily_active_users[idx_max]];
    color = IMPRINT_PALETTE[4], markersize = 16, strokewidth = 0,
)
scatter!(
    ax, [day[1]], [daily_active_users[1]];
    color = PAGE_BG, markersize = 18, strokewidth = 2, strokecolor = BRAND,
)
scatter!(
    ax, [day[end]], [daily_active_users[end]];
    color = BRAND, markersize = 22, strokewidth = 2, strokecolor = PAGE_BG,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
