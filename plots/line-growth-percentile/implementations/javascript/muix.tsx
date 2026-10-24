// anyplot.ai
// line-growth-percentile: Pediatric Growth Chart with Percentile Curves
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 83/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { LinePlot, MarkPlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const BANDS: Array<{ loIdx: number; hiIdx: number; opacity: number }> = [
  { loIdx: 0, hiIdx: 1, opacity: 0.25 },
  { loIdx: 1, hiIdx: 2, opacity: 0.17 },
  { loIdx: 2, hiIdx: 4, opacity: 0.09 },
  { loIdx: 4, hiIdx: 5, opacity: 0.17 },
  { loIdx: 5, hiIdx: 6, opacity: 0.25 },
];
const X_PAD_SHARE = 0.02;
const Y_TOP_PAD_SHARE = 0.08;
const X_TICK_COUNT = 7;
const Y_TICK_COUNT = 6;

// Columns: set these to your data's column names
const AGE = "Age (months)"; // role: age_months
const P3 = "P3"; // role: percentile_3
const P10 = "P10"; // role: percentile_10
const P25 = "P25"; // role: percentile_25
const P50 = "P50"; // role: percentile_50
const P75 = "P75"; // role: percentile_75
const P90 = "P90"; // role: percentile_90
const P97 = "P97"; // role: percentile_97
const PATIENT = "Patient weight (kg)"; // role: measurement
const PERCENTILES = [P3, P10, P25, P50, P75, P90, P97] as const;

// Data: replace this block with your own records
const Z_SCORES = [-1.88, -1.28, -0.67, 0, 0.67, 1.28, 1.88];
const PATIENT_VISITS: Record<number, number> = {
  0: 3.35,
  2: 5.1,
  4: 6.45,
  6: 7.65,
  9: 9.05,
  12: 10.2,
  15: 10.95,
  18: 11.65,
  21: 12.3,
  24: 13.15,
  30: 14.5,
  36: 15.9,
};

const data: Array<{
  [AGE]: number;
  [P3]: number;
  [P10]: number;
  [P25]: number;
  [P50]: number;
  [P75]: number;
  [P90]: number;
  [P97]: number;
  [PATIENT]: number | null;
}> = [];

for (let ageM = 0; ageM <= 36; ageM += 1) {
  const med = 16 - 12.7 * Math.exp(-0.057 * ageM);
  const cv = 0.128 - (0.013 * ageM) / 36;
  data.push({
    [AGE]: ageM,
    [P3]: Number((med * (1 + Z_SCORES[0] * cv)).toFixed(2)),
    [P10]: Number((med * (1 + Z_SCORES[1] * cv)).toFixed(2)),
    [P25]: Number((med * (1 + Z_SCORES[2] * cv)).toFixed(2)),
    [P50]: Number((med * (1 + Z_SCORES[3] * cv)).toFixed(2)),
    [P75]: Number((med * (1 + Z_SCORES[4] * cv)).toFixed(2)),
    [P90]: Number((med * (1 + Z_SCORES[5] * cv)).toFixed(2)),
    [P97]: Number((med * (1 + Z_SCORES[6] * cv)).toFixed(2)),
    [PATIENT]: ageM in PATIENT_VISITS ? PATIENT_VISITS[ageM] : null,
  });
}

// Plot: reads only data and the constants above
const ageUnitMatch = AGE.match(/\(([^)]+)\)/);
const ageUnitRaw = ageUnitMatch ? ageUnitMatch[1] : "";
const ageUnit = ageUnitRaw === "months" ? "mo" : ageUnitRaw;

const measUnitMatch = PATIENT.match(/\(([^)]+)\)/);
const measUnit = measUnitMatch ? measUnitMatch[1] : "";

const sortedData = [...data].sort((a, b) => a[AGE] - b[AGE]);
const ages = sortedData.map((d) => d[AGE]);
const rawXMin = Math.min(...ages);
const rawXMax = Math.max(...ages);
const xSpan = rawXMax - rawXMin;
const X_MIN = rawXMin - xSpan * X_PAD_SHARE;
const X_MAX = rawXMax + xSpan * X_PAD_SHARE;

const allRefValues = sortedData.flatMap((d) =>
  PERCENTILES.map((col) => d[col]),
);
const patientPoints = sortedData
  .filter((d) => d[PATIENT] !== null)
  .map((d) => ({ age: d[AGE], weight: d[PATIENT]! }));

const maxRefVal = Math.max(
  ...allRefValues,
  ...patientPoints.map((p) => p.weight),
);
const Y_MIN = 0;
const Y_MAX = maxRefVal * (1 + Y_TOP_PAD_SHARE);

const BAND_COLOR = t.palette[2];
const PATIENT_COLOR = t.palette[0];

const PATIENT_ID = "patient";

const series = [
  ...PERCENTILES.map((col) => ({
    type: "line" as const,
    id: col,
    label: col,
    xAxisId: "age",
    yAxisId: "weight",
    data: sortedData.map((d) => d[col]),
    color: BAND_COLOR,
    curve: "linear" as const,
    showMark: false,
  })),
  {
    type: "line" as const,
    id: PATIENT_ID,
    label: PATIENT,
    xAxisId: "age",
    yAxisId: "weight",
    data: sortedData.map((d) => d[PATIENT]),
    color: PATIENT_COLOR,
    curve: "linear" as const,
    connectNulls: true,
    showMark: true,
    shape: "circle" as const,
  },
];

// Filled bands and right-margin labels: the parts line series can't draw
function BandLayer() {
  const xScale = useXScale("age") as (v: number) => number;
  const yScale = useYScale("weight") as (v: number) => number;

  return (
    <g>
      {/* Filled percentile bands (P3→P97) */}
      {BANDS.map((band, idx) => {
        const loCol = PERCENTILES[band.loIdx];
        const hiCol = PERCENTILES[band.hiIdx];
        let d = `M ${xScale(sortedData[0][AGE]).toFixed(1)} ${yScale(
          sortedData[0][hiCol],
        ).toFixed(1)}`;
        for (let i = 1; i < sortedData.length; i += 1) {
          d += ` L ${xScale(sortedData[i][AGE]).toFixed(1)} ${yScale(
            sortedData[i][hiCol],
          ).toFixed(1)}`;
        }
        for (let i = sortedData.length - 1; i >= 0; i -= 1) {
          d += ` L ${xScale(sortedData[i][AGE]).toFixed(1)} ${yScale(
            sortedData[i][loCol],
          ).toFixed(1)}`;
        }
        d += " Z";

        return (
          <path
            key={`band-${idx}`}
            d={d}
            fill={BAND_COLOR}
            fillOpacity={band.opacity}
            stroke="none"
          />
        );
      })}
    </g>
  );
}

function PercentileLabels() {
  const xScale = useXScale("age") as (v: number) => number;
  const yScale = useYScale("weight") as (v: number) => number;
  const rightEdgeX = xScale(rawXMax) + 12;
  const lastRow = sortedData[sortedData.length - 1];

  return (
    <g>
      {PERCENTILES.map((col) => {
        const isMedian = col === P50;
        return (
          <text
            key={`lbl-${col}`}
            x={rightEdgeX}
            y={yScale(lastRow[col])}
            fontSize={isMedian ? 16 : 14}
            fontWeight={isMedian ? 700 : 600}
            fontFamily={MONO}
            fill={isMedian ? t.ink : BAND_COLOR}
            dominantBaseline="middle"
          >
            {col}
          </text>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerHeight = 84;
  const chartHeight = height - headerHeight;
  const firstVisit = patientPoints[0];
  const lastVisit = patientPoints[patientPoints.length - 1];

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: headerHeight,
          padding: "14px 72px 4px 104px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxSizing: "border-box",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: t.ink,
              lineHeight: 1.2,
            }}
          >
            line-growth-percentile · javascript · muix · anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: MONO,
            }}
          >
            WHO-like reference (synthetic, {P3}–{P97}, {rawXMin}–{rawXMax}{" "}
            {ageUnit}) · {patientPoints.length} visits (
            {firstVisit.weight.toFixed(2)} {measUnit} at {firstVisit.age}{" "}
            {ageUnit} → {lastVisit.weight.toFixed(2)} {measUnit} at{" "}
            {lastVisit.age} {ageUnit})
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            fontSize: 15,
            color: t.ink,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: PATIENT_COLOR,
                display: "inline-block",
              }}
            />
            <span>{PATIENT}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 24,
                height: 3,
                borderRadius: 2,
                background: BAND_COLOR,
                display: "inline-block",
              }}
            />
            <span>Median ({P50})</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 20,
                height: 14,
                borderRadius: 3,
                background: `${BAND_COLOR}42`,
                border: `1.5px solid ${BAND_COLOR}`,
                display: "inline-block",
                boxSizing: "border-box",
              }}
            />
            <span>
              Reference bands ({P3}–{P97})
            </span>
          </div>
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={{ left: 20, right: 72, top: 20, bottom: 20 }}
        skipAnimation
        series={series}
        xAxis={[
          {
            id: "age",
            data: ages,
            scaleType: "linear",
            min: X_MIN,
            max: X_MAX,
            height: 60,
            tickNumber: X_TICK_COUNT,
            label: AGE,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
            valueFormatter: (v: number) => String(v),
          },
        ]}
        yAxis={[
          {
            id: "weight",
            scaleType: "linear",
            min: Y_MIN,
            max: Y_MAX,
            width: 84,
            tickNumber: Y_TICK_COUNT,
            label: PATIENT,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: MONO,
            },
            valueFormatter: (v: number) => String(v),
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiLineChart-line": {
            strokeWidth: 1.3,
            strokeOpacity: 0.58,
            strokeLinecap: "round",
            strokeLinejoin: "round",
          },
          [`& .MuiLineChart-line[data-series="${P50}"]`]: {
            strokeWidth: 2.8,
            strokeOpacity: 0.94,
          },
          [`& .MuiLineChart-line[data-series="${PATIENT_ID}"]`]: {
            strokeWidth: 3.2,
            strokeOpacity: 1,
          },
          [`& .MuiLineChart-mark[data-series="${PATIENT_ID}"]`]: {
            r: 6.2,
            fill: PATIENT_COLOR,
            stroke: t.pageBg,
            strokeWidth: 2,
          },
        }}
      >
        <ChartsGrid horizontal />
        <BandLayer />
        <LinePlot />
        <MarkPlot />
        <PercentileLabels />
        <ChartsXAxis axisId="age" />
        <ChartsYAxis axisId="weight" />
      </ChartsContainer>
    </div>
  );
}
