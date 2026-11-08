// anyplot.ai
// eye-diagram-basic: Signal Integrity Eye Diagram
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TIME_BINS = 100; // density cells across the time window
const VOLTAGE_BINS = 56; // density cells across the voltage range
const DENSITY_LABEL = "Traces per cell (log scale)";
const TITLE = "eye-diagram-basic · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_W = 150;

// Columns: set these to your data's column names
const TIME = "Time (UI)"; // role: time
const VOLTAGE = "Voltage (V)"; // role: voltage
const TRACE = "Trace"; // role: trace_id

// Data: replace this block with your own records, one object per row
// 300 overlaid 2-UI windows of a simulated NRZ bit stream, bit edges at 0, 1 and 2 UI: sigmoid band-limited edges,
// Gaussian timing jitter (sigma 3 % of a UI) and additive noise (sigma 5 % of the 1 V swing)
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
  const randn = () => {
    const u = rand() || 1e-10;
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
  };
  const edge = (x: number) => 1 / (1 + Math.exp(-12 * x));
  const rows: { [TIME]: number; [VOLTAGE]: number; [TRACE]: number }[] = [];
  for (let trace = 1; trace <= 300; trace++) {
    const b0 = rand() > 0.5 ? 1 : 0;
    const b1 = rand() > 0.5 ? 1 : 0;
    const b2 = rand() > 0.5 ? 1 : 0;
    const b3 = rand() > 0.5 ? 1 : 0;
    const j0 = randn() * 0.03;
    const j1 = randn() * 0.03;
    const j2 = randn() * 0.03;
    for (let s = 0; s < 200; s++) {
      const time = (s / 199) * 2;
      const voltage =
        b0 +
        (b1 - b0) * edge(time - j0) +
        (b2 - b1) * edge(time - 1 - j1) +
        (b3 - b2) * edge(time - 2 - j2) +
        randn() * 0.05;
      rows.push({ [TIME]: time, [VOLTAGE]: voltage, [TRACE]: trace });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const samples = data.filter((d) => Number.isFinite(d[TIME]) && Number.isFinite(d[VOLTAGE]));
const timeMin = samples.reduce((m, d) => Math.min(m, d[TIME]), Infinity);
const timeMax = samples.reduce((m, d) => Math.max(m, d[TIME]), -Infinity);
const voltageMin = samples.reduce((m, d) => Math.min(m, d[VOLTAGE]), Infinity);
const voltageMax = samples.reduce((m, d) => Math.max(m, d[VOLTAGE]), -Infinity);
const timeStep = (timeMax - timeMin) / TIME_BINS;
const voltageStep = (voltageMax - voltageMin) / VOLTAGE_BINS;

// Trace density: the number of distinct traces that pass through each time × voltage cell
const tracesByCell = new Map<number, Set<number>>();
samples.forEach((d) => {
  const ti = Math.min(Math.floor((d[TIME] - timeMin) / timeStep), TIME_BINS - 1);
  const vi = Math.min(Math.floor((d[VOLTAGE] - voltageMin) / voltageStep), VOLTAGE_BINS - 1);
  const key = ti * VOLTAGE_BINS + vi;
  const traces = tracesByCell.get(key) ?? new Set<number>();
  traces.add(d[TRACE]);
  tracesByCell.set(key, traces);
});
const cells = [...tracesByCell].map(([key, traces]) => {
  const ti = Math.floor(key / VOLTAGE_BINS);
  const vi = key % VOLTAGE_BINS;
  return {
    key,
    time0: timeMin + ti * timeStep,
    time1: timeMin + (ti + 1) * timeStep,
    voltage0: voltageMin + vi * voltageStep,
    voltage1: voltageMin + (vi + 1) * voltageStep,
    logCount: Math.log(traces.size),
  };
});
const logCountMax = Math.max(...cells.map((c) => c.logCount));
const traceCount = new Set(samples.map((d) => d[TRACE])).size;
const subtitle = `${traceCount} overlaid traces · ${Math.round(samples.length / traceCount)} samples per trace · ${TIME_BINS} × ${VOLTAGE_BINS} density cells`;

function DensityCells() {
  const xScale = useXScale() as unknown as (v: number) => number;
  const yScale = useYScale() as unknown as (v: number) => number;
  const colorScale = useZColorScale() as unknown as (v: number) => string;
  return (
    <g>
      {cells.map((c) => {
        const x0 = xScale(c.time0);
        const y1 = yScale(c.voltage1);
        return (
          <rect
            key={c.key}
            x={x0}
            y={y1}
            width={xScale(c.time1) - x0 + 0.5}
            height={yScale(c.voltage0) - y1 + 0.5}
            fill={colorScale(c.logCount)}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <ChartsDataProvider
        width={width - LEGEND_W}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={{ top: 12, right: 24, bottom: 20, left: 24 }}
        xAxis={[
          {
            scaleType: "linear",
            min: timeMin,
            max: timeMax,
            label: TIME,
            height: 68,
            tickNumber: 9,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: voltageMin,
            max: voltageMax,
            label: VOLTAGE,
            width: 84,
            tickNumber: 8,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            colorMap: { type: "continuous", min: 0, max: logCountMax, color: [t.seq[0], t.seq[1]] },
          },
        ]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "middle", horizontal: "end" }}
          legendDirection="vertical"
          sx={{ width, height: height - TITLE_H }}
        >
          <Box
            sx={{
              gridArea: "legend",
              width: LEGEND_W,
              height: 460,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <Typography sx={{ fontSize: 15, color: t.ink, textAlign: "center", lineHeight: 1.3, maxWidth: 120, mb: "10px" }}>
              {DENSITY_LABEL}
            </Typography>
            <ContinuousColorLegend
              direction="vertical"
              thickness={20}
              labelPosition="end"
              minLabel={({ value }) => String(Math.round(Math.exp(Number(value))))}
              maxLabel={({ value }) => String(Math.round(Math.exp(Number(value))))}
              sx={{ flex: 1, color: t.inkSoft, fontSize: 14 }}
            />
          </Box>
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <DensityCells />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
