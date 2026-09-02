// anyplot.ai
// map-route-path: Route Path Map
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ChartsLegend, ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data: deterministic LCG — a cycling commute route through Amsterdam ----
function makeLcg(seed: number) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

const N_POINTS = 140;
const START = { lon: 4.868, lat: 52.358 }; // home, Amsterdam-West
const TARGET = { lon: 4.907, lat: 52.376 }; // office, Amsterdam city centre
const LON_SPAN = TARGET.lon - START.lon;
const LAT_SPAN = TARGET.lat - START.lat;

// Longitude advances monotonically with progress fraction `f`, which rules
// out any self-crossing loop by construction — the lateral wiggle (mostly on
// latitude) then reads as organic canal-side turns, not a tangled scribble.
const lon: number[] = [];
const lat: number[] = [];
for (let i = 0; i < N_POINTS; i++) {
  const f = i / (N_POINTS - 1);
  const lonWiggle = Math.sin(f * Math.PI * 3) * 0.0012 * Math.sin(f * Math.PI);
  const latWiggle = Math.sin(f * Math.PI * 4 + 0.6) * 0.0022 * Math.sin(f * Math.PI);
  const lonNoise = (rand() - 0.5) * 0.0004;
  const latNoise = (rand() - 0.5) * 0.0004;
  lon.push(START.lon + LON_SPAN * f + lonWiggle + lonNoise);
  lat.push(START.lat + LAT_SPAN * f + latWiggle + latNoise);
}

const routePoints = lon.map((x, i) => ({ x, y: lat[i], z: i, id: i }));

const TITLE_HEIGHT = 60;
const MARGIN = { left: 130, right: 70, top: 40, bottom: 80 };

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        paddingTop: "20px",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        map-route-path · javascript · muix · anyplot.ai
      </Typography>
      <ChartContainer
        width={width}
        height={height - TITLE_HEIGHT}
        margin={MARGIN}
        skipAnimation
        xAxis={[
          {
            id: "lonAxis",
            data: lon,
            scaleType: "linear",
            label: "Longitude (°)",
            valueFormatter: (v: number) => v.toFixed(3),
            tickLabelStyle: { fontSize: 14 },
            labelFontSize: 16,
          },
        ]}
        yAxis={[
          {
            id: "latAxis",
            scaleType: "linear",
            label: "Latitude (°)",
            valueFormatter: (v: number) => v.toFixed(3),
            // MUI X reserves label clearance as `tickFontSize + tickSize + 10`
            // (a fixed constant, not the tick label's actual text width), so a
            // 6-digit coordinate tick ("52.367") needs a much larger tickFontSize
            // than it's actually rendered at to avoid the axis title overlapping
            // it — tickLabelStyle.fontSize below restores the real 14px size.
            tickFontSize: 55,
            tickLabelStyle: { fontSize: 14 },
            labelFontSize: 16,
          },
        ]}
        zAxis={[
          {
            id: "seqAxis",
            min: 0,
            max: N_POINTS - 1,
            colorMap: { type: "continuous", color: [t.seq[0], t.seq[1]] },
          },
          // Start/End markers opt out of the sequence colorMap (which every
          // scatter series would inherit by default via `defaultZAxisId`)
          // so their fixed `color` below is used verbatim.
          { id: "plainAxis" },
        ]}
        series={[
          {
            type: "line",
            xAxisId: "lonAxis",
            yAxisId: "latAxis",
            data: lat,
            showMark: false,
            color: t.inkSoft,
            curve: "linear",
          },
          {
            type: "scatter",
            xAxisId: "lonAxis",
            yAxisId: "latAxis",
            zAxisId: "seqAxis",
            data: routePoints,
            markerSize: 5,
            valueFormatter: (v) => `waypoint ${v.z}`,
          },
          {
            type: "scatter",
            xAxisId: "lonAxis",
            yAxisId: "latAxis",
            zAxisId: "plainAxis",
            data: [{ x: lon[0], y: lat[0], id: "start" }],
            color: t.palette[0],
            markerSize: 12,
            label: "Start",
          },
          {
            type: "scatter",
            xAxisId: "lonAxis",
            yAxisId: "latAxis",
            zAxisId: "plainAxis",
            data: [{ x: lon[N_POINTS - 1], y: lat[N_POINTS - 1], id: "end" }],
            color: t.palette[4],
            markerSize: 12,
            label: "End",
          },
        ]}
        sx={{
          "& .MuiChartsLegend-label": { fontSize: "14px" },
          "& .MuiLineElement-root": { strokeWidth: 2, strokeOpacity: 0.6 },
        }}
      >
        <ChartsGrid horizontal vertical />
        <LinePlot />
        <ScatterPlot />
        <ChartsXAxis />
        <ChartsYAxis />
        <ChartsLegend position={{ horizontal: "left", vertical: "top" }} direction="row" />
        <ContinuousColorLegend
          axisDirection="z"
          axisId="seqAxis"
          position={{ horizontal: "left", vertical: "bottom" }}
          direction="row"
          minLabel="Start"
          maxLabel="End"
          length={220}
          thickness={10}
        />
        <ChartsTooltip trigger="item" />
      </ChartContainer>
    </Box>
  );
}
