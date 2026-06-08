# anyplot.ai
# swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-06-08

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint categorical palette — hybrid-v3 canonical order
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — Arm A / Experimental (brand green)
    colorant"#C475FD",  # 2 — Arm B / Control (lavender)
    colorant"#4467A3",  # 3 — Partial Response (blue)
    colorant"#BD8233",  # 4 — Complete Response (ochre)
    colorant"#AE3030",  # 5 — Progressive Disease (matte red)
]
const ANYPLOT_AMBER = colorant"#DDCC77"  # Adverse Event — warning anchor (outside categorical pool)

# Data: Phase II oncology trial — anti-PD-1 + chemo (Arm A) vs. chemo alone (Arm B)
n_patients = 25
treatment_arms = vcat(fill("Arm A", 13), fill("Arm B", 12))
Random.shuffle!(treatment_arms)

durations = [
    treatment_arms[i] == "Arm A" ? 10.0 + rand() * 42.0 : 4.0 + rand() * 28.0
    for i in 1:n_patients
]

is_ongoing = [
    treatment_arms[i] == "Arm A" ? rand() < 0.46 : rand() < 0.25
    for i in 1:n_patients
]

# Sort ascending by duration so longest bar appears at top of chart
perm           = sortperm(durations)
durations      = durations[perm]
treatment_arms = treatment_arms[perm]
is_ongoing     = is_ongoing[perm]
patient_labels = ["PT-$(lpad(p, 3, '0'))" for p in perm]

# Clinical events: (patient_idx, time_weeks, event_type)
event_data = Tuple{Int, Float64, String}[]

for i in 1:n_patients
    dur = durations[i]
    arm = treatment_arms[i]

    # Partial response — earlier in treatment, higher rate in Arm A
    if dur > 6.0 && rand() < (arm == "Arm A" ? 0.65 : 0.40)
        t = dur * (0.15 + rand() * 0.35)
        push!(event_data, (i, t, "partial_response"))
    end

    # Complete response — sustained duration required, predominantly Arm A
    if dur > 22.0 && rand() < (arm == "Arm A" ? 0.38 : 0.10)
        t = dur * (0.42 + rand() * 0.28)
        push!(event_data, (i, t, "complete_response"))
    end

    # Progressive disease — usually near end, more common in control arm
    if !is_ongoing[i] && rand() < (arm == "Arm B" ? 0.58 : 0.22)
        t = min(dur * (0.68 + rand() * 0.28), dur * 0.97)
        push!(event_data, (i, t, "progressive_disease"))
    end

    # Adverse event — random, any patient
    if rand() < 0.38
        t = dur * (0.08 + rand() * 0.65)
        push!(event_data, (i, t, "adverse_event"))
    end
end

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str    = "swimmer-clinical-timeline · julia · makie · anyplot.ai"
n_chars      = length(title_str)
ratio        = n_chars > 67 ? 67 / n_chars : 1.0
title_sz     = round(Int, 20 * ratio)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_sz,
    titlecolor         = INK,
    xlabel             = "Time on Study (weeks)",
    xlabelsize         = 13,
    xlabelcolor        = INK,
    xticklabelsize     = 11,
    yticklabelsize     = 9,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = true,
    ygridvisible       = false,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yticks             = (1:n_patients, patient_labels),
)

# Horizontal bars — one per patient, colored by treatment arm
bar_h = 0.52
for i in 1:n_patients
    c = treatment_arms[i] == "Arm A" ? IMPRINT_PALETTE[1] : IMPRINT_PALETTE[2]
    poly!(ax, Rect2f(0.0, i - bar_h / 2, durations[i], bar_h);
        color       = (c, 0.78),
        strokewidth = 0.5,
        strokecolor = c,
    )
end

# Rightward arrows for patients still on treatment at data cutoff
arrow_len = 2.8
for i in 1:n_patients
    if is_ongoing[i]
        c = treatment_arms[i] == "Arm A" ? IMPRINT_PALETTE[1] : IMPRINT_PALETTE[2]
        arrows!(ax, [durations[i]], [Float64(i)], [arrow_len], [0.0];
            color     = c,
            arrowsize = 12,
            linewidth = 2.5,
        )
    end
end

# Event markers — one scatter call per event type
evt_styles = Dict(
    "partial_response"    => (IMPRINT_PALETTE[3], :utriangle, 13),
    "complete_response"   => (IMPRINT_PALETTE[4], :star5,     15),
    "progressive_disease" => (IMPRINT_PALETTE[5], :dtriangle, 13),
    "adverse_event"       => (ANYPLOT_AMBER,       :xcross,    12),
)

for evt_type in ("partial_response", "complete_response", "progressive_disease", "adverse_event")
    subset = filter(e -> e[3] == evt_type, event_data)
    isempty(subset) && continue
    xs = [e[2] for e in subset]
    ys = [Float64(e[1]) for e in subset]
    c, mk, sz = evt_styles[evt_type]
    scatter!(ax, xs, ys;
        color       = c,
        marker      = mk,
        markersize  = sz,
        strokewidth = 1.0,
        strokecolor = PAGE_BG,
    )
end

max_dur = maximum(durations)
xlims!(ax, -0.8, max_dur + 7.0)
ylims!(ax, 0.25, n_patients + 0.75)

# Legend
elem_a  = PolyElement(polycolor = (IMPRINT_PALETTE[1], 0.78), polystrokecolor = IMPRINT_PALETTE[1], polystrokewidth = 0.5)
elem_b  = PolyElement(polycolor = (IMPRINT_PALETTE[2], 0.78), polystrokecolor = IMPRINT_PALETTE[2], polystrokewidth = 0.5)
elem_pr = MarkerElement(color = IMPRINT_PALETTE[3], marker = :utriangle, markersize = 12, strokecolor = PAGE_BG, strokewidth = 1)
elem_cr = MarkerElement(color = IMPRINT_PALETTE[4], marker = :star5,     markersize = 12, strokecolor = PAGE_BG, strokewidth = 1)
elem_pd = MarkerElement(color = IMPRINT_PALETTE[5], marker = :dtriangle, markersize = 12, strokecolor = PAGE_BG, strokewidth = 1)
elem_ae = MarkerElement(color = ANYPLOT_AMBER,       marker = :xcross,    markersize = 12, strokecolor = PAGE_BG, strokewidth = 1)

Legend(fig[1, 2],
    [elem_a, elem_b, elem_pr, elem_cr, elem_pd, elem_ae],
    ["Arm A — Experimental", "Arm B — Control", "Partial Response", "Complete Response", "Progressive Disease", "Adverse Event"],
    "Treatment & Events";
    framevisible      = true,
    framecolor        = INK_SOFT,
    backgroundcolor   = ELEVATED_BG,
    labelcolor        = INK,
    titlecolor        = INK,
    labelfontsize   = 10,
    titlefontsize   = 11,
    patchsize       = (22, 14),
    rowgap          = 4,
)

colsize!(fig.layout, 1, Relative(0.78))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
