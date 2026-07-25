# anyplot.ai
# rose-basic: Basic Rose Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-07-25

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
# Monthly rainfall for a temperate coastal city — wetter autumn/winter,
# drier summer, a natural 12-month cycle where the circular layout maps
# directly onto the calendar.
months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
n_months = length(months)
base_rainfall_mm = [82, 68, 74, 58, 52, 41, 33, 38, 54, 71, 88, 95]
rainfall_mm = base_rainfall_mm .+ randn(n_months) .* 4

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = PolarAxis(
    fig[1, 1];
    theta_0             = -pi / 2,  # January starts at 12 o'clock
    direction           = -1,       # clockwise, matching calendar order
    backgroundcolor     = PAGE_BG,
    title               = "Monthly Rainfall · rose-basic · julia · makie · anyplot.ai",
    titlesize           = 20,
    titlecolor          = INK,
    thetaticks          = (range(0, 2pi, length = n_months + 1)[1:n_months], months),
    thetaticklabelsize  = 14,
    thetaticklabelcolor = INK_SOFT,
    thetagridvisible    = false,
    rticks              = 0:20:100,
    rtickformat         = vs -> ["$(round(Int, v)) mm" for v in vs],
    rtickangle          = 13pi / 12,  # Jul–Aug gap — the driest wedges, keeps labels off the tall bars
    rticklabelsize      = 15,
    rticklabelcolor     = INK_SOFT,
    rgridvisible        = true,
    rgridcolor          = RGBAf(INK.r, INK.g, INK.b, 0.15),
    rgridwidth          = 1,
    spinecolor          = INK_SOFT,
    spinewidth          = 1,
    rlimits             = (0, 110),
)

# Equal-angle wedges, radius proportional to value — filled with `band!`
# since it (unlike `poly!`) respects the PolarAxis per-vertex transform
# and traces a true curved arc rather than a straight-edged rectangle.
# Fill alpha is ramped by value (spec's "varying saturation" option) so the
# wettest months read as the visual focal point; the peak/trough wedges also
# get a heavier outline as an explicit callout for the seasonal story.
theta = range(0, 2pi, length = n_months + 1)[1:n_months]
half_width = (2pi / n_months) * 0.9 / 2
n_arc_samples = 40
rmin, rmax = extrema(rainfall_mm)
peak_idx, trough_idx = argmax(rainfall_mm), argmin(rainfall_mm)

for (i, (t, rv)) in enumerate(zip(theta, rainfall_mm))
    ts = collect(range(t - half_width, t + half_width, length = n_arc_samples))
    alpha = 0.55 + 0.45 * (rv - rmin) / (rmax - rmin)
    wedge_color = RGBAf(IMPRINT_PALETTE[1].r, IMPRINT_PALETTE[1].g, IMPRINT_PALETTE[1].b, alpha)
    band!(
        ax, ts, zeros(n_arc_samples), fill(rv, n_arc_samples);
        color = wedge_color,
    )

    if i == peak_idx || i == trough_idx
        outline_theta = vcat(t - half_width, ts, t + half_width)
        outline_r     = vcat(0.0, fill(rv, n_arc_samples), 0.0)
        lines!(ax, outline_theta, outline_r; color = INK, linewidth = 2.5)
    end
end

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
