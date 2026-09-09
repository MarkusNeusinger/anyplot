# anyplot.ai
# scatter-regression-lowess: Scatter Plot with LOWESS Regression
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-09

using CairoMakie
using Colors
using Random

# --- Theme tokens -------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND       = colorant"#009E73"  # Imprint palette position 1 — scatter points
const CURVE_COLOR = colorant"#4467A3"  # Imprint palette position 3 — LOWESS fit

# --- Data: light-response curve of net photosynthesis -------------------------
Random.seed!(42)
n = 200
light_intensity = sort(rand(n) .* 2000)  # PAR, μmol photons m⁻² s⁻¹
true_response = 13.5 .* (1 .- exp.(-light_intensity ./ 280)) .- 0.0016 .* light_intensity
net_photosynthesis = true_response .+ randn(n) .* 0.9  # μmol CO2 m⁻² s⁻¹

# --- LOWESS smoothing: local weighted linear regression, tricube weights ------
frac = 0.35
k = ceil(Int, frac * n)
eval_x = collect(range(minimum(light_intensity), maximum(light_intensity); length = 200))
fitted_y = similar(eval_x)

for (i, x0) in enumerate(eval_x)
    dist = abs.(light_intensity .- x0)
    d_max = sort(dist)[k]
    w = ifelse.(dist .<= d_max, (1 .- clamp.(dist ./ d_max, 0, 1) .^ 3) .^ 3, 0.0)

    sw = sum(w)
    sx = sum(w .* light_intensity)
    sy = sum(w .* net_photosynthesis)
    sxx = sum(w .* light_intensity .^ 2)
    sxy = sum(w .* light_intensity .* net_photosynthesis)

    slope = (sw * sxy - sx * sy) / (sw * sxx - sx^2)
    intercept = (sy - slope * sx) / sw
    fitted_y[i] = intercept + slope * x0
end

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "scatter-regression-lowess · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Light Intensity (μmol photons m⁻² s⁻¹)",
    ylabel            = "Net Photosynthesis (μmol CO₂ m⁻² s⁻¹)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

scatter!(
    ax, light_intensity, net_photosynthesis;
    color = (BRAND, 0.65), markersize = 11,
    strokecolor = PAGE_BG, strokewidth = 1,
    label = "Observations",
)
lines!(ax, eval_x, fitted_y; color = CURVE_COLOR, linewidth = 3, label = "LOWESS fit")

axislegend(ax; position = :lt, backgroundcolor = ELEVATED_BG, labelcolor = INK, framevisible = false)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
