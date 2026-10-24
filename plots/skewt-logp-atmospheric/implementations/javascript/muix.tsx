// anyplot.ai
// skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-26
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsClipPath } from "@mui/x-charts/ChartsClipPath";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "skewt-logp-atmospheric · javascript · muix · anyplot.ai";
const P_SURFACE = 1000;
const P_TOP = 100;
const KAPPA = 0.286;
const R_D = 287;
const C_P = 1004;
const L_V = 2.5e6;
const EPSILON = 0.622;
const DRY_ADIABAT_ANCHORS_C = [-30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
const MOIST_ADIABAT_ANCHORS_C = [0, 5, 10, 15, 20, 25, 30];
const MIXING_RATIOS_G_PER_KG = [0.4, 1, 2, 3, 5, 8, 12, 16, 20];
const MIXING_RATIO_MIN_PRESSURE = 400;
const PRESSURE_TICKS = [1000, 850, 700, 500, 400, 300, 250, 200, 150, 100];

// Columns: set these to your data's column names
const PRESSURE = "Pressure (hPa)"; // role: pressure
const TEMPERATURE = "Temperature (°C, at surface)"; // role: temperature
const DEWPOINT = "Dewpoint (°C)"; // role: dewpoint

// Data: replace this block with your own records
const SURFACE_TEMP_C = 22;
const LAPSE_RATE_C_PER_KM = 6.5;
const TROPOPAUSE_HEIGHT_M = 11000;
const TROPOPAUSE_TEMP_C = SURFACE_TEMP_C - LAPSE_RATE_C_PER_KM * (TROPOPAUSE_HEIGHT_M / 1000);

const data = [];
for (let p = P_SURFACE; p >= P_TOP; p -= 25) {
  const heightM = 44330 * (1 - Math.pow(p / P_SURFACE, 1 / 5.255));
  const tempC =
    heightM <= TROPOPAUSE_HEIGHT_M
      ? SURFACE_TEMP_C - LAPSE_RATE_C_PER_KM * (heightM / 1000)
      : TROPOPAUSE_TEMP_C + 0.6 * ((heightM - TROPOPAUSE_HEIGHT_M) / 1000);
  const es = 6.112 * Math.exp((17.67 * tempC) / (tempC + 243.5));
  const dryingWithHeight = 0.15 + 0.55 * Math.max(0, (p - P_TOP) / (P_SURFACE - P_TOP));
  const embeddedMoistLayer = 0.35 * Math.exp(-Math.pow((p - 400) / 60, 2));
  const rh = Math.min(0.95, dryingWithHeight + embeddedMoistLayer);
  const e = rh * es;
  const logRatio = Math.log(e / 6.112);
  const dewpointC = (243.5 * logRatio) / (17.67 - logRatio);
  data.push({
    [PRESSURE]: p,
    [TEMPERATURE]: tempC,
    [DEWPOINT]: dewpointC,
  });
}

// Plot: reads only data and the constants above
const pressureLevels = data.map((row) => Number(row[PRESSURE]));
const soundingTempC = data.map((row) => Number(row[TEMPERATURE]));
const soundingDewpointC = data.map((row) => Number(row[DEWPOINT]));

const moistAdiabatCurves = MOIST_ADIABAT_ANCHORS_C.map((surfaceTempC) => {
  const points = [{ p: P_SURFACE, t: surfaceTempC }];
  let temp = surfaceTempC;
  let pressure = P_SURFACE;
  const stepHpa = 5;
  while (pressure > P_TOP) {
    const es = 6.112 * Math.exp((17.67 * temp) / (temp + 243.5));
    const ws = (EPSILON * es) / (pressure - es);
    const tempK = temp + 273.15;
    const numerator = 1 + (L_V * ws) / (R_D * tempK);
    const denominator = 1 + (L_V * L_V * ws * EPSILON) / (C_P * R_D * tempK * tempK);
    const dTdP = ((tempK / pressure) * (R_D / C_P) * numerator) / denominator;
    temp += dTdP * -stepHpa;
    pressure -= stepHpa;
    points.push({ p: pressure, t: temp });
  }
  return points;
});

function SkewTOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  const drawingArea = useDrawingArea();

  const pxPerDegC = xScale(1) - xScale(0);
  const ySurf = yScale(P_SURFACE);

  const isotherms = [];
  for (let tc = -120; tc <= 120; tc += 10) {
    const x1 = xScale(tc);
    const y1 = ySurf;
    const y2 = yScale(P_TOP);
    const x2 = xScale(tc + (ySurf - y2) / pxPerDegC);
    isotherms.push({ tc, x1, y1, x2, y2 });
  }

  const dryAdiabatPaths = DRY_ADIABAT_ANCHORS_C.map((anchor) => {
    const thetaK = anchor + 273.15;
    return pressureLevels
      .map((p, i) => {
        const tempC = thetaK * Math.pow(p / P_SURFACE, KAPPA) - 273.15;
        const y = yScale(p);
        const x = xScale(tempC + (ySurf - y) / pxPerDegC);
        return `${i === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  });

  const moistAdiabatPaths = moistAdiabatCurves.map((curve) =>
    curve
      .map((pt, i) => {
        const y = yScale(pt.p);
        const x = xScale(pt.t + (ySurf - y) / pxPerDegC);
        return `${i === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ")
  );

  const mixingRatioLevels = pressureLevels.filter((p) => p >= MIXING_RATIO_MIN_PRESSURE);
  const mixingRatioPaths = MIXING_RATIOS_G_PER_KG.map((wG) => {
    const w = wG / 1000;
    return mixingRatioLevels
      .map((p, i) => {
        const vp = (w * p) / (EPSILON + w);
        const logRatio = Math.log(vp / 6.112);
        const tempC = (243.5 * logRatio) / (17.67 - logRatio);
        const y = yScale(p);
        const x = xScale(tempC + (ySurf - y) / pxPerDegC);
        return `${i === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  });

  const tempPath = pressureLevels
    .map((p, i) => {
      const y = yScale(p);
      const x = xScale(soundingTempC[i] + (ySurf - y) / pxPerDegC);
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  const dewpointPath = pressureLevels
    .map((p, i) => {
      const y = yScale(p);
      const x = xScale(soundingDewpointC[i] + (ySurf - y) / pxPerDegC);
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  const markerLevels = pressureLevels
    .map((p, i) => ({ p, i }))
    .filter((_, i) => i % 4 === 0 && i !== pressureLevels.length - 1);

  const clipId = "skewt-plot-clip";
  const legendX = drawingArea.left + 18;
  const legendY = drawingArea.top + 18;
  const legendRows = [
    { label: "Temperature", color: t.palette[0], dash: "0" },
    { label: "Dewpoint", color: t.palette[2], dash: "10 6" },
    { label: "Dry adiabat", color: t.inkSoft, dash: "6 4" },
    { label: "Moist adiabat", color: t.inkSoft, dash: "1 4" },
    { label: "Mixing ratio", color: t.inkSoft, dash: "3 2 1 2" },
  ];
  const legendRowHeight = 26;
  const legendHeight = legendRows.length * legendRowHeight + 16;
  const legendWidth = 190;

  return (
    <>
      <ChartsClipPath id={clipId} />
      <g clipPath={`url(#${clipId})`}>
        {isotherms.map((l) => (
          <line
            key={`iso-${l.tc}`}
            x1={l.x1}
            y1={l.y1}
            x2={l.x2}
            y2={l.y2}
            stroke={l.tc === 0 ? t.amber : t.grid}
            strokeWidth={l.tc === 0 ? 2.5 : 1.25}
          />
        ))}
        {dryAdiabatPaths.map((d, i) => (
          <path
            key={`dry-${i}`}
            d={d}
            fill="none"
            stroke={t.inkSoft}
            strokeWidth={1.25}
            strokeDasharray="6 4"
            opacity={0.55}
          />
        ))}
        {moistAdiabatPaths.map((d, i) => (
          <path
            key={`moist-${i}`}
            d={d}
            fill="none"
            stroke={t.inkSoft}
            strokeWidth={1.25}
            strokeDasharray="1 4"
            opacity={0.55}
          />
        ))}
        {mixingRatioPaths.map((d, i) => (
          <path
            key={`mix-${i}`}
            d={d}
            fill="none"
            stroke={t.inkSoft}
            strokeWidth={1.25}
            strokeDasharray="3 2 1 2"
            opacity={0.45}
          />
        ))}
        <path d={dewpointPath} fill="none" stroke={t.palette[2]} strokeWidth={3} strokeDasharray="10 6" />
        <path d={tempPath} fill="none" stroke={t.palette[0]} strokeWidth={3.5} />
        {markerLevels.map(({ p, i }) => {
          const y = yScale(p);
          const skew = (ySurf - y) / pxPerDegC;
          const xT = xScale(soundingTempC[i] + skew);
          const xD = xScale(soundingDewpointC[i] + skew);
          return (
            <g key={`mark-${p}`}>
              <circle cx={xT} cy={y} r={5} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={1.5} />
              <circle cx={xD} cy={y} r={5} fill={t.palette[2]} stroke={t.pageBg} strokeWidth={1.5} />
            </g>
          );
        })}
      </g>
      <rect
        x={legendX}
        y={legendY}
        width={legendWidth}
        height={legendHeight}
        rx={6}
        fill={t.elevatedBg}
        stroke={t.grid}
        strokeWidth={1}
      />
      {legendRows.map((row, i) => {
        const rowY = legendY + 16 + i * legendRowHeight + legendRowHeight / 2;
        return (
          <g key={row.label}>
            <line
              x1={legendX + 14}
              y1={rowY}
              x2={legendX + 44}
              y2={rowY}
              stroke={row.color}
              strokeWidth={row.dash === "0" ? 3 : 2}
              strokeDasharray={row.dash === "0" ? undefined : row.dash}
            />
            <text x={legendX + 54} y={rowY} dy="0.32em" fontSize={15} fill={t.ink}>
              {row.label}
            </text>
          </g>
        );
      })}
    </>
  );
}

export default function Chart() {
  const titleHeight = 52;
  const chartHeight = window.ANYPLOT_SIZE.height - titleHeight;

  return (
    <Box
      sx={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography sx={{ fontSize: 22, fontWeight: 600, pl: 1, pt: 0.5, color: t.ink }}>
        {TITLE}
      </Typography>
      <ChartsContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        margin={{ top: 20, right: 32, bottom: 24, left: 24 }}
        series={[]}
        skipAnimation
        xAxis={[
          {
            id: "temperature",
            scaleType: "linear",
            min: -40,
            max: 45,
            height: 64,
            label: TEMPERATURE,
            tickNumber: 9,
          },
        ]}
        yAxis={[
          {
            id: "pressure",
            scaleType: "log",
            reverse: true,
            min: P_TOP,
            max: P_SURFACE,
            width: 88,
            label: PRESSURE,
            tickInterval: PRESSURE_TICKS,
            valueFormatter: (v) => `${v}`,
          },
        ]}
      >
        <SkewTOverlay />
        <ChartsXAxis axisId="temperature" />
        <ChartsYAxis axisId="pressure" />
      </ChartsContainer>
    </Box>
  );
}
