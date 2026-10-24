// anyplot.ai
// climograph-walter-lieth: Walter-Lieth Climate Diagram
// Library: muix 9.0.0 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-15

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Columns
const STATION = "Station name";
const ELEVATION = "Elevation (m a.s.l.)";
const MONTH = "Month";
const TEMPERATURE = "Temperature (°C)";
const PRECIPITATION = "Precipitation (mm)";

// Data — Lisbon, Portugal (1991–2020 climate normals)
const data = [
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Jan", [TEMPERATURE]: 11.3, [PRECIPITATION]: 77 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Feb", [TEMPERATURE]: 12.4, [PRECIPITATION]: 62 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Mar", [TEMPERATURE]: 14.2, [PRECIPITATION]: 54 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Apr", [TEMPERATURE]: 16.0, [PRECIPITATION]: 42 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "May", [TEMPERATURE]: 18.5, [PRECIPITATION]: 36 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Jun", [TEMPERATURE]: 21.7, [PRECIPITATION]: 13 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Jul", [TEMPERATURE]: 24.2, [PRECIPITATION]: 4 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Aug", [TEMPERATURE]: 24.5, [PRECIPITATION]: 5 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Sep", [TEMPERATURE]: 22.3, [PRECIPITATION]: 25 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Oct", [TEMPERATURE]: 18.6, [PRECIPITATION]: 65 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Nov", [TEMPERATURE]: 14.8, [PRECIPITATION]: 93 },
  { [STATION]: "Lisbon, Portugal", [ELEVATION]: 77, [MONTH]: "Dec", [TEMPERATURE]: 11.7, [PRECIPITATION]: 91 },
];

// Constants
const TITLE = "climograph-walter-lieth · javascript · muix · anyplot.ai";
const TEMP_AXIS_ID = "tempY";
const PRECIP_AXIS_ID = "precipR";
const WL_PRECIP_RATIO = 2;
const Y_PAD_TOP = 0.075;
const HUMID_FILL = t.palette[2];
const ARID_FILL = t.palette[4];
const FROST_COLOR = t.palette[5];
const ELEVATION_UNIT = ELEVATION.match(/\(([^)]+)\)/)?.[1] ?? "";
const TEMP_UNIT = TEMPERATURE.match(/\(([^)]+)\)/)?.[1] ?? "";
const PRECIP_UNIT = PRECIPITATION.match(/\(([^)]+)\)/)?.[1] ?? "";

const stationName = data[0][STATION];
const elevation = data[0][ELEVATION];
const months = data.map((d) => d[MONTH]);
const temperature = data.map((d) => d[TEMPERATURE]);
const precipitation = data.map((d) => d[PRECIPITATION]);
const precipScaled = precipitation.map((p) => p / WL_PRECIP_RATIO);

const annualMeanTemp = (temperature.reduce((a, b) => a + b, 0) / data.length).toFixed(1);
const annualTotalPrecip = precipitation.reduce((a, b) => a + b, 0);

const minDataVal = Math.min(0, ...temperature, ...precipScaled);
const maxDataVal = Math.max(...temperature, ...precipScaled);
const yMin = minDataVal < 0 ? Math.floor(minDataVal * (1 + Y_PAD_TOP)) : 0;
const yMax = Math.ceil(maxDataVal * (1 + Y_PAD_TOP));

const hasFrostMonths = temperature.some((temp) => temp < 0);
const legendItems = [
  { color: ARID_FILL, isLine: true, label: TEMPERATURE },
  { color: HUMID_FILL, isLine: true, label: PRECIPITATION },
  { color: `${HUMID_FILL}61`, border: HUMID_FILL, label: "Humid period" },
  { color: `${ARID_FILL}61`, border: ARID_FILL, label: "Arid period" },
  ...(hasFrostMonths
    ? [{ color: `${FROST_COLOR}D9`, border: FROST_COLOR, label: "Frost month (< 0 °C)" }]
    : []),
];

const CHART_SERIES = [
  {
    id: "temp",
    label: TEMPERATURE,
    data: temperature,
    type: "line",
    color: ARID_FILL,
    yAxisId: TEMP_AXIS_ID,
    showMark: false,
    curve: "linear",
  },
  {
    id: "precip",
    label: PRECIPITATION,
    data: precipScaled,
    type: "line",
    color: HUMID_FILL,
    yAxisId: TEMP_AXIS_ID,
    showMark: false,
    curve: "linear",
  },
];

function WalterLiethFill() {
  const { top, height } = useDrawingArea();
  const xScale = useXScale("x");
  const yScale = useYScale(TEMP_AXIS_ID);

  if (!xScale || !yScale || !xScale.bandwidth) return null;

  const bw = xScale.bandwidth();
  const xs = months.map((m) => (xScale(m) ?? 0) + bw / 2);
  const tys = temperature.map((v) => yScale(v) ?? 0);
  const pys = precipScaled.map((v) => yScale(v) ?? 0);

  const elems = [];

  for (let i = 0; i < months.length - 1; i++) {
    const x0 = xs[i];
    const x1 = xs[i + 1];
    const ty0 = tys[i];
    const ty1 = tys[i + 1];
    const py0 = pys[i];
    const py1 = pys[i + 1];
    const h0 = precipScaled[i] > temperature[i];
    const h1 = precipScaled[i + 1] > temperature[i + 1];

    if (h0 === h1) {
      elems.push(
        <polygon
          key={`f${i}`}
          points={`${x0},${py0} ${x1},${py1} ${x1},${ty1} ${x0},${ty0}`}
          fill={h0 ? HUMID_FILL : ARID_FILL}
          fillOpacity={0.38}
        />
      );
    } else {
      const denom = py1 - py0 - (ty1 - ty0);
      const frac = Math.abs(denom) > 0.01 ? (ty0 - py0) / denom : 0.5;
      const xc = x0 + (x1 - x0) * frac;
      const yc = ty0 + (ty1 - ty0) * frac;
      elems.push(
        <polygon
          key={`f${i}a`}
          points={`${x0},${py0} ${xc},${yc} ${x0},${ty0}`}
          fill={h0 ? HUMID_FILL : ARID_FILL}
          fillOpacity={0.38}
        />,
        <polygon
          key={`f${i}b`}
          points={`${xc},${yc} ${x1},${py1} ${x1},${ty1}`}
          fill={h1 ? HUMID_FILL : ARID_FILL}
          fillOpacity={0.38}
        />
      );
    }
  }

  for (let i = 0; i < months.length; i++) {
    if (temperature[i] < 0) {
      const xi = xs[i];
      elems.push(
        <rect
          key={`frost${i}`}
          x={xi - bw / 2}
          y={top + height + 2}
          width={bw}
          height={6}
          fill={FROST_COLOR}
          fillOpacity={0.85}
        />
      );
    }
  }

  for (let i = 0; i < months.length - 1; i++) {
    const x0 = xs[i];
    const x1 = xs[i + 1];
    elems.push(
      <line
        key={`tl-${i}`}
        x1={x0}
        y1={tys[i]}
        x2={x1}
        y2={tys[i + 1]}
        stroke={ARID_FILL}
        strokeWidth={3}
        strokeLinecap="round"
      />,
      <line
        key={`pl-${i}`}
        x1={x0}
        y1={pys[i]}
        x2={x1}
        y2={pys[i + 1]}
        stroke={HUMID_FILL}
        strokeWidth={3}
        strokeLinecap="round"
      />
    );
  }

  return <g>{elems}</g>;
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - 172;
  const chartW = width - 48;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        px: "24px",
        pt: "18px",
        pb: "14px",
        boxSizing: "border-box",
      }}
    >
      <Box sx={{ textAlign: "center", mb: "10px" }}>
        <Typography sx={{ color: t.ink, fontWeight: 700, fontSize: 22, lineHeight: 1.3 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, mt: "4px" }}>
          {`${stationName} (${elevation} ${ELEVATION_UNIT}) · Annual mean ${annualMeanTemp} ${TEMP_UNIT} · Annual total ${annualTotalPrecip} ${PRECIP_UNIT} · 1991–2020 climate normals`}
        </Typography>
      </Box>

      <ChartsContainer
        width={chartW}
        height={chartH}
        series={CHART_SERIES}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: months,
            height: 44,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: TEMP_AXIS_ID,
            position: "left",
            min: yMin,
            max: yMax,
            width: 76,
            label: TEMPERATURE,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
          {
            id: PRECIP_AXIS_ID,
            position: "right",
            min: yMin,
            max: yMax,
            width: 84,
            label: PRECIPITATION,
            valueFormatter: (v) => `${v * WL_PRECIP_RATIO}`,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        margin={{ top: 16, right: 24, bottom: 16, left: 24 }}
        skipAnimation
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <WalterLiethFill />
        <LinePlot />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId={TEMP_AXIS_ID} />
        <ChartsYAxis axisId={PRECIP_AXIS_ID} disableLine />
      </ChartsContainer>

      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: "28px",
          mt: "8px",
          flexWrap: "wrap",
        }}
      >
        {legendItems.map((item) => (
          <Box key={item.label} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {item.isLine ? (
              <Box
                sx={{
                  width: 26,
                  height: 3.5,
                  bgcolor: item.color,
                  borderRadius: "2px",
                  flexShrink: 0,
                }}
              />
            ) : (
              <Box
                sx={{
                  width: 22,
                  height: 14,
                  bgcolor: item.color,
                  border: `1.5px solid ${item.border}`,
                  borderRadius: "3px",
                  flexShrink: 0,
                }}
              />
            )}
            <Typography sx={{ fontSize: 14, color: t.inkSoft }}>{item.label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
