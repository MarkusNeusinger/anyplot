// anyplot.ai
// skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsClipPath } from "@mui/x-charts/ChartsClipPath";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const KAPPA = 0.286; // Rd / cp, dry adiabatic exponent
const R_D = 287; // J / (kg K), gas constant of dry air
const C_P = 1004; // J / (kg K), specific heat of dry air at constant pressure
const L_V = 2.5e6; // J / kg, latent heat of vaporization
const EPSILON = 0.622; // Rd / Rv
const FREEZING_C = 0; // isotherm drawn heavier
const MANDATORY_LEVELS = [1000, 850, 700, 500, 400, 300, 250, 200, 150, 100]; // hPa, pressure ticks
const ISOTHERM_STEP = 10; // °C
const DRY_ADIABAT_STEP = 10; // °C of potential temperature
const MOIST_ADIABAT_STEP = 5; // °C at the bottom level
const MIXING_RATIOS = [0.4, 1, 2, 3, 5, 8, 12, 16, 20]; // g/kg
const MIXING_RATIO_TOP = 400; // hPa, mixing-ratio lines stop here by convention
const CURVE_STEP_HPA = 5; // integration and sampling step of the reference curves
const X_PAD_SHARE = 0.04; // window padding as a share of the window width

// Columns: set these to your data's column names
const PRESSURE = "Pressure (hPa)"; // role: pressure
const TEMPERATURE = "Temperature (°C)"; // role: temperature
const DEWPOINT = "Dewpoint (°C)"; // role: dewpoint

// Data: replace this block with your own records, one object per row
// Warm-season radiosonde sounding every 25 hPa: standard lapse rate to an 11 km tropopause,
// air drying with height and a moist layer near 400 hPa.
const data: Record<string, number>[] = [];
for (let p = 1000; p >= 100; p -= 25) {
  const heightM = 44330 * (1 - Math.pow(p / 1000, 1 / 5.255));
  const temp = heightM <= 11000 ? 22 - 6.5 * (heightM / 1000) : 22 - 6.5 * 11 + 0.6 * ((heightM - 11000) / 1000);
  const rh = Math.min(0.95, 0.15 + 0.55 * Math.max(0, (p - 100) / 900) + 0.35 * Math.exp(-(((p - 400) / 60) ** 2)));
  const logRatio = Math.log((rh * 6.112 * Math.exp((17.67 * temp) / (temp + 243.5))) / 6.112);
  data.push({
    [PRESSURE]: p,
    [TEMPERATURE]: Number(temp.toFixed(1)),
    [DEWPOINT]: Number(((243.5 * logRatio) / (17.67 - logRatio)).toFixed(1)),
  });
}

// Plot: reads only data and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const levels = [...data].sort((a, b) => b[PRESSURE] - a[PRESSURE]);
const pBottom = levels[0][PRESSURE];
const pTop = levels[levels.length - 1][PRESSURE];
const logSpan = Math.log(pBottom / pTop);

// Layout: the drawing area's aspect sets how far a 45° isotherm shifts per unit of log-pressure
const HEADER_H = 84;
const LEGEND_H = 48;
const MARGIN = { top: 16, right: 32, bottom: 8, left: 16 };
const X_AXIS_H = 64;
const Y_AXIS_W = 72;
const chartH = H - HEADER_H - LEGEND_H;
const aspect = (chartH - MARGIN.top - MARGIN.bottom - X_AXIS_H) / (W - MARGIN.left - MARGIN.right - Y_AXIS_W);

// Temperature window at the bottom level: the smallest span that holds every skewed
// level with padding (a fixed point, since the skew itself scales with the span)
const heightShare = levels.map((d) => Math.log(pBottom / d[PRESSURE]) / logSpan);
let span = Math.max(...levels.map((d) => d[TEMPERATURE])) - Math.min(...levels.map((d) => d[DEWPOINT]));
let skewedMin = 0;
for (let k = 0; k < 40; k += 1) {
  const skewed = levels.flatMap((d, i) => [d[TEMPERATURE], d[DEWPOINT]].map((v) => v + heightShare[i] * aspect * span));
  skewedMin = Math.min(...skewed);
  span = (Math.max(...skewed) - skewedMin) / (1 - 2 * X_PAD_SHARE);
}
const xMin = skewedMin - X_PAD_SHARE * span;
const xMax = xMin + span;
const topShift = aspect * span; // °C an isotherm moves right between the bottom and the top

// Reference families as (temperature, pressure) polylines, covering the window
const pressureGrid: number[] = [];
for (let p = pBottom; p >= pTop; p -= CURVE_STEP_HPA) pressureGrid.push(p);
const isotherms: number[] = [];
for (let tc = Math.ceil((xMin - topShift) / ISOTHERM_STEP) * ISOTHERM_STEP; tc <= xMax; tc += ISOTHERM_STEP) {
  isotherms.push(tc);
}
const thetaMax = (xMax - topShift + 273.15) / Math.pow(pTop / pBottom, KAPPA) - 273.15;
const dryAdiabats: { t: number; p: number }[][] = [];
for (let th = Math.ceil(xMin / DRY_ADIABAT_STEP) * DRY_ADIABAT_STEP; th <= thetaMax; th += DRY_ADIABAT_STEP) {
  dryAdiabats.push(pressureGrid.map((p) => ({ t: (th + 273.15) * Math.pow(p / pBottom, KAPPA) - 273.15, p })));
}
const moistAdiabats: { t: number; p: number }[][] = [];
for (let t0 = Math.ceil(xMin / MOIST_ADIABAT_STEP) * MOIST_ADIABAT_STEP; t0 <= xMax; t0 += MOIST_ADIABAT_STEP) {
  let temp = t0;
  const curve = [{ t: temp, p: pBottom }];
  for (let p = pBottom; p - CURVE_STEP_HPA >= pTop; p -= CURVE_STEP_HPA) {
    const es = 6.112 * Math.exp((17.67 * temp) / (temp + 243.5));
    const ws = (EPSILON * es) / (p - es);
    const tk = temp + 273.15;
    const dTdP = ((tk / p) * (R_D / C_P) * (1 + (L_V * ws) / (R_D * tk))) / (1 + (L_V * L_V * ws * EPSILON) / (C_P * R_D * tk * tk));
    temp -= dTdP * CURVE_STEP_HPA;
    curve.push({ t: temp, p: p - CURVE_STEP_HPA });
  }
  moistAdiabats.push(curve);
}
const mixingLines = MIXING_RATIOS.map((w) =>
  pressureGrid
    .filter((p) => p >= MIXING_RATIO_TOP)
    .map((p) => {
      const logRatio = Math.log(((w / 1000) * p) / (EPSILON + w / 1000) / 6.112);
      return { t: (243.5 * logRatio) / (17.67 - logRatio), p };
    }),
);
const tempProfile = levels.map((d) => ({ t: d[TEMPERATURE], p: d[PRESSURE] }));
const dewProfile = levels.map((d) => ({ t: d[DEWPOINT], p: d[PRESSURE] }));
const tempColor = t.palette[0];
const dewColor = t.palette[2]; // moisture in blue

const title = "skewt-logp-atmospheric · javascript · muix · anyplot.ai";
const subtitle = `${levels.length} levels · ${PRESSURE} ${pBottom} to ${pTop} · bottom level: ${TEMPERATURE} ${levels[0][TEMPERATURE]}, ${DEWPOINT} ${levels[0][DEWPOINT]}`;
const legendItems = [
  { label: TEMPERATURE.replace(/ \(.*\)$/, ""), color: tempColor, width: 3.5, dash: "" },
  { label: DEWPOINT.replace(/ \(.*\)$/, ""), color: dewColor, width: 3, dash: "10 6" },
  { label: "Isotherm", color: t.inkSoft, width: 1.5, dash: "", opacity: 0.5 },
  { label: "Dry adiabat", color: t.inkSoft, width: 1.5, dash: "6 4" },
  { label: "Moist adiabat", color: t.inkSoft, width: 1.75, dash: "1.5 4" },
  { label: "Mixing ratio", color: t.inkSoft, width: 1.5, dash: "3 2 1 2" },
];

function SkewTLayer() {
  const xScale = useXScale("temperature") as (v: number) => number;
  const yScale = useYScale("pressure") as (v: number) => number;
  const pxPerDeg = xScale(1) - xScale(0);
  const toPath = (pts: { t: number; p: number }[]) =>
    pts
      .map((pt, i) => `${i === 0 ? "M" : "L"}${xScale(pt.t + (yScale(pBottom) - yScale(pt.p)) / pxPerDeg)},${yScale(pt.p)}`)
      .join(" ");
  return (
    <>
      <ChartsClipPath id="skewt-clip" />
      <g clipPath="url(#skewt-clip)">
        {isotherms.map((tc) => (
          <path
            key={`iso-${tc}`}
            d={toPath([{ t: tc, p: pBottom }, { t: tc, p: pTop }])}
            stroke={t.inkSoft}
            strokeOpacity={tc === FREEZING_C ? 0.6 : 0.35}
            strokeWidth={tc === FREEZING_C ? 2 : 1.25}
          />
        ))}
        {dryAdiabats.map((c, i) => (
          <path key={`dry-${i}`} d={toPath(c)} fill="none" stroke={t.inkSoft} strokeWidth={1.25} strokeDasharray="6 4" opacity={0.55} />
        ))}
        {moistAdiabats.map((c, i) => (
          <path key={`moist-${i}`} d={toPath(c)} fill="none" stroke={t.inkSoft} strokeWidth={1.75} strokeDasharray="1.5 4" strokeLinecap="round" opacity={0.75} />
        ))}
        {mixingLines.map((c, i) => (
          <path key={`mix-${i}`} d={toPath(c)} fill="none" stroke={t.inkSoft} strokeWidth={1.25} strokeDasharray="3 2 1 2" opacity={0.5} />
        ))}
        <path d={toPath(dewProfile)} fill="none" stroke={dewColor} strokeWidth={3} strokeDasharray="10 6" />
        <path d={toPath(tempProfile)} fill="none" stroke={tempColor} strokeWidth={3.5} />
      </g>
      {/* Level markers stay unclipped: the window holds every skewed level, and the top and bottom levels sit on the edges */}
      {levels.map((d) => {
        const skew = (yScale(pBottom) - yScale(d[PRESSURE])) / pxPerDeg;
        return (
          <g key={`level-${d[PRESSURE]}`}>
            <circle cx={xScale(d[DEWPOINT] + skew)} cy={yScale(d[PRESSURE])} r={3.5} fill={dewColor} stroke={t.pageBg} strokeWidth={1} />
            <circle cx={xScale(d[TEMPERATURE] + skew)} cy={yScale(d[PRESSURE])} r={3.5} fill={tempColor} stroke={t.pageBg} strokeWidth={1} />
          </g>
        );
      })}
    </>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        margin={MARGIN}
        series={[]}
        skipAnimation
        xAxis={[
          {
            id: "temperature",
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: `${TEMPERATURE}, isotherms skewed 45°`,
            height: X_AXIS_H,
            tickNumber: 8,
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
        yAxis={[
          {
            id: "pressure",
            scaleType: "log",
            reverse: true,
            min: pTop,
            max: pBottom,
            label: PRESSURE,
            width: Y_AXIS_W,
            tickInterval: MANDATORY_LEVELS.filter((p) => p >= pTop && p <= pBottom),
            valueFormatter: (v: number) => `${v}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <SkewTLayer />
        <ChartsXAxis axisId="temperature" />
        <ChartsYAxis axisId="pressure" />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 24,
          fontSize: 16,
          color: t.ink,
        }}
      >
        {legendItems.map((item) => (
          <span key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width={34} height={10}>
              <line
                x1={1}
                y1={5}
                x2={33}
                y2={5}
                stroke={item.color}
                strokeWidth={item.width}
                strokeDasharray={item.dash || undefined}
                strokeOpacity={item.opacity ?? 1}
              />
            </svg>
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}
