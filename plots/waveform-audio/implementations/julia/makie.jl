# anyplot.ai
# waveform-audio: Audio Waveform Plot
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 93/100 | Created: 2026-06-03

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# Data — synthetic seismogram: noise floor, P-wave arrival at 5 s, S-wave at 10 s
sample_rate = 1000
duration    = 30.0
n_samples   = Int(sample_rate * duration)
t           = collect(range(0.0, duration, length=n_samples))

noise = 0.015 .* randn(n_samples)

p_start = Int(5.0 * sample_rate) + 1
p_end   = min(Int(8.0 * sample_rate), n_samples)
t_p     = collect(range(0.0, 3.0, length=p_end - p_start + 1))
p_wave  = zeros(n_samples)
p_wave[p_start:p_end] .= 0.3 .* sin.(2π .* 3.0 .* t_p) .* exp.(-0.6 .* t_p)

s_start = Int(10.0 * sample_rate) + 1
s_end   = min(Int(22.0 * sample_rate), n_samples)
t_s     = collect(range(0.0, 12.0, length=s_end - s_start + 1))
s_wave  = zeros(n_samples)
s_wave[s_start:s_end] .= 0.85 .* sin.(2π .* 1.5 .* t_s) .* exp.(-0.25 .* t_s)

amplitude = noise .+ p_wave .+ s_wave

# Min/max envelope (100 ms windows) avoids aliasing artifacts in dense waveform
window_size = 100
n_windows   = div(n_samples, window_size)
t_env   = [mean(t[(i-1)*window_size+1 : i*window_size]) for i in 1:n_windows]
amp_min = [minimum(amplitude[(i-1)*window_size+1 : i*window_size]) for i in 1:n_windows]
amp_max = [maximum(amplitude[(i-1)*window_size+1 : i*window_size]) for i in 1:n_windows]

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "Earthquake Seismogram · waveform-audio · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Time (seconds)",
    ylabel             = "Normalized Amplitude",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = true,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yticks             = [-1.0, -0.5, 0.0, 0.5, 1.0],
)

xlims!(ax, 0.0, duration)
ylims!(ax, -1.1, 1.1)

# Subtle noise-floor shading behind waveform (±2σ of background noise)
noise_floor = 0.015 * 2.0
band!(ax, [0.0, duration], [-noise_floor, -noise_floor], [noise_floor, noise_floor];
    color = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.08))

# Waveform envelope fill — semi-transparent Imprint brand green with stroke outline
band!(ax, t_env, amp_min, amp_max; color = (BRAND, 0.72))
lines!(ax, t_env, amp_max; color = (BRAND, 0.55), linewidth = 0.8)
lines!(ax, t_env, amp_min; color = (BRAND, 0.55), linewidth = 0.8)

# Zero-amplitude reference line
hlines!(ax, [0.0]; color = INK_SOFT, linewidth = 1.2)

# P-wave and S-wave arrival annotations
vlines!(ax, [5.0]; color = RGBAf(INK.r, INK.g, INK.b, 0.35), linewidth = 1.0, linestyle = :dash)
vlines!(ax, [10.0]; color = RGBAf(INK.r, INK.g, INK.b, 0.35), linewidth = 1.0, linestyle = :dash)
text!(ax, 5.3, 0.95; text = "P-wave", fontsize = 11, color = INK_SOFT, align = (:left, :top))
text!(ax, 10.3, 0.95; text = "S-wave", fontsize = 11, color = INK_SOFT, align = (:left, :top))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
