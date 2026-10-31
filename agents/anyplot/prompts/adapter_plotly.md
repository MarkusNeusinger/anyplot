<!--
plotly's passages of the adapter prompt (PB-2a of step 4, 2026-10-31): `policy.adapter_instruction("plotly")` puts the
section below right after the Python adapter prompt, whose matplotlib conventions (the `savefig` statement, `figsize`
and `dpi`, `FuncFormatter`, `AutoDateLocator`) it replaces for plotly; every other library's instruction is unchanged.
Measured in the renderer image on 2026-10-31 through the figure mode (`harness.py --figure`): the pinned JSON save
(`code/figure.py`) drawn at the canvas by the device scale, `separators` writing the plot language's marks in every
d3 format, tz-aware timestamps drawn as given unless converted, plotly express switching `scatter` to WebGL above
1,000 points, and a WebGL trace failing the render (`draw NoWebGL`; a 3D scene drew nothing but its colour bar).
`tests/unit/agents/runtime/test_policy.py` runs the idioms through both validator profiles, and
`tests/unit/agents/code/test_profile_python_figure_image.py` renders them. This comment never reaches a model.
-->

## plotly: what replaces the matplotlib conventions above

This plot is plotly. Where the rules above name matplotlib (`savefig`, `figsize`, `dpi`, `FuncFormatter`, `AutoDateLocator`, a `VQ-03` or `VQ-06` gate line, the drawn texts the server checks), these rules apply instead:

- **The save.** The code ends on one protected statement, `fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")`, which writes the figure as JSON; the server draws it in a browser at the canvas, scaled so a 16:9 size fills 3200 by 1800 pixels and a size narrower than 4:3 fills 2400 by 2400. Keep it as it is, the last statement of the file, and set no `width`, `height` or `autosize` anywhere else: the size in it fixes how large the text is against the plot. Never call `write_image`, `write_html`, `show`, `to_image` or `to_html`, and never import `plotly.io`, `plotly.offline` or `kaleido`: the server saves the figure, and the downloaded code gets plotly's own PNG and HTML save back.
- **No render check of the texts.** A plotly render has no probe, so the reviewer looks for each requested text in the image, and no gate counts labels or checks decimal marks: the code alone keeps them right.
- **Theme.** Colour every part from the theme tokens: `paper_bgcolor=PAGE_BG, plot_bgcolor=PAGE_BG`, `font={"family": "Helvetica, Arial, sans-serif", "color": INK}`, axis `gridcolor=GRID` and `tickfont={"color": INK_SOFT}`, never a `template` the code does not already use and never a font that is not on the machine (a web font falls back to the default).
- **Missing values.** `df` keeps a missing cell as `<NA>` or `NaT`. Drop the rows a mark needs before you plot or compute from them (`df.dropna(subset=[X, Y])`), so no category called `<NA>` and no point at a missing date appears; to draw a gap in a line instead, keep the row and hand the column over as floats (`df[Y].astype("float64")`): plotly breaks the line at a `NaN`.
- **Dates.** A timestamp column with a UTC offset is time-zone aware, and plotly draws the clock time it is given: convert it once to UTC, `days = dated[DAY].dt.tz_convert("UTC").dt.tz_localize(None) if dated[DAY].dt.tz is not None else dated[DAY]`, and write the axis with `tickformat="%d.%m.%Y"`, so the server's render and the downloaded page show the same dates.
- **Numbers.** Set the plot language's marks once on the layout, `separators=DECIMAL + THOUSANDS` (`","` and `"."` for `de`), and every number plotly writes with a d3 format follows them: `tickformat=",.0f"` on a value axis, `hovertemplate="%{y:,.1f}"` and `texttemplate="%{y:,.0f}"` on a trace. A number you write into a string yourself (an annotation, a title) takes the f-string swap above, `f"{v:,.0f}".replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS)`. Write the words for large numbers yourself (divide, then `ticksuffix=" Mio."`), since `tickformat="~s"` writes English SI letters.
- **No WebGL.** The server's browser has no WebGL: a WebGL trace fails the render. Never use `go.Scattergl`, `Scatterpolargl`, `Splom`, `Scatter3d`, `Surface`, `Mesh3d`, `Cone`, `Volume`, `Isosurface`, `Parcoords` or a map trace (`Scattermap`, `Densitymap`, `Choroplethmap`), and pass `render_mode="svg"` to every plotly express `scatter`, `line`, `scatter_polar`, `line_polar` and `ecdf`, which switch to WebGL above 1,000 points.
- **Safe code.** Import only `plotly.graph_objects`, `plotly.express`, `plotly.subplots`, `plotly.colors` and `plotly.figure_factory` besides the computing modules above; never `plotly.express.data` or another bundled dataset, and no image or URL in the layout (`layout.images`, `source=`).
