# anyplot.ai: the drawn texts of a Makie plot, for the agents' closing reply.
#
# The renderer's Julia row loads this file with `-L` after the precompile workload
# (agents/renderer/commands.py, JULIA_TEXT_PROBE), before `plot.jl`. It only registers an
# `atexit` hook: when the plot has ended and saved `plot-<theme>.png`, the hook walks the
# current figure's blocks and writes `texts-<theme>.json`, `{"entries": [[kind, text], ...]}`,
# which the harness's exec mode turns into `probe-<theme>.json` under the probe's caps
# (`harness.collect_text_probe`). Kinds as the matplotlib probe names them: the axes' titles,
# axis labels and tick labels, the legends' titles and entries, a `Label` block (the title when
# no axes has one and it is larger than every other label), a colorbar's label and ticks, and
# every other text plot in an axes (`text!`, bar labels) as an annotation.
#
# Best-effort: a block that cannot be read is left out, any other failure writes
# `{"error": <exception type>}` instead, and the hook prints nothing, so
# the plot's exit code and stderr stay its own; a plot without Makie, without a figure or
# without its PNG writes nothing. The plot code runs before the hook and can change what it
# reads; the harness and the agents read the result as untrusted data.

module AnyplotTextProbe

const THEME = get(ENV, "ANYPLOT_THEME", "light")
const LIMIT = 2000
const MAKIE = Base.PkgId(Base.UUID("ee78f7c6-11fb-53f2-987a-cfe4a2b5a57a"), "Makie")

"""The strings of a text attribute's value: a string, a vector of them, or anything else as `string`."""
function strings(value)::Vector{String}
    value isa AbstractString && return [String(value)]
    value isa AbstractVector && return reduce(vcat, (strings(item) for item in value); init = String[])
    value === nothing && return String[]
    return [string(value)]
end

function json_string(text::AbstractString)
    io = IOBuffer()
    print(io, '"')
    for char in text
        if !isvalid(char)
            print(io, '?')
        elseif char == '"'
            print(io, "\\\"")
        elseif char == '\\'
            print(io, "\\\\")
        elseif char < ' '
            print(io, ' ')
        else
            print(io, char)
        end
    end
    print(io, '"')
    return String(take!(io))
end

function write_report(text::AbstractString)
    open("texts-$(THEME).json", "w") do handle
        write(handle, text)
    end
end

"""Every text plot under `plot`, depth first."""
function text_plots!(found, M, plot)
    plot isa M.Text && push!(found, plot)
    for child in plot.plots
        text_plots!(found, M, child)
    end
    return found
end

shown(attribute) = attribute[] !== false

function entries(M, figure)
    found = Tuple{String,String}[]
    add(kind, value) = length(found) < LIMIT && append!(found, ((kind, text) for text in strings(value) if !isempty(strip(text))))
    labels = Tuple{Float64,String}[]
    titled = false
    for block in figure.content
        # One block that cannot be read (a version's other field names) leaves the others' texts.
        try
            if block isa M.Axis
                if shown(block.titlevisible) && !isempty(strip(string(block.title[])))
                    titled = true
                    add("title", block.title[])
                end
                shown(block.subtitlevisible) && add("subtitle", block.subtitle[])
                shown(block.xlabelvisible) && add("x axis label", block.xlabel[])
                shown(block.ylabelvisible) && add("y axis label", block.ylabel[])
                shown(block.xticklabelsvisible) && add("x tick label", block.xaxis.ticklabels[])
                shown(block.yticklabelsvisible) && add("y tick label", block.yaxis.ticklabels[])
                for plot in block.scene.plots
                    for text in text_plots!(Any[], M, plot)
                        shown(text.visible) && add("annotation", text.text[])
                    end
                end
            elseif block isa M.Legend
                for (title, group) in block.entrygroups[]
                    add("legend text", title)
                    for entry in group
                        add("legend text", entry.label[])
                    end
                end
            elseif block isa M.Colorbar
                shown(block.labelvisible) && add("colorbar label", block.label[])
                shown(block.ticklabelsvisible) && add("colorbar tick label", block.axis.ticklabels[])
            elseif block isa M.Label
                shown(block.visible) && push!(labels, (Float64(block.fontsize[]), string(block.text[])))
            elseif hasproperty(block, :title)  # Axis3, PolarAxis
                titled = titled || !isempty(strip(string(block.title[])))
                add("title", block.title[])
            end
        catch
        end
    end
    # A `Label` is the title only when no axes has one and it is larger than every other label: panel letters or
    # column headers of one size are no title.
    largest = isempty(labels) ? 0.0 : maximum(first, labels)
    alone = count(label -> first(label) == largest, labels) == 1
    for label in labels
        add(!titled && alone && first(label) == largest ? "title" : "text", label[2])
    end
    return found
end

function probe()
    M = get(Base.loaded_modules, MAKIE, nothing)
    (M === nothing || !isfile("plot-$(THEME).png")) && return
    try
        figure = M.current_figure()
        figure === nothing && return
        pairs = entries(M, figure)
        write_report("{\"entries\":[" * join(("[" * json_string(k) * "," * json_string(t) * "]" for (k, t) in pairs), ",") * "]}")
    catch exception
        try
            write_report("{\"error\":" * json_string(string(nameof(typeof(exception)))) * "}")
        catch
        end
    end
    return
end

end

atexit(AnyplotTextProbe.probe)
