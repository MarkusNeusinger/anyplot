// anyplot.ai
// line-growth-percentile: Pediatric Growth Chart with Percentile Curves
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-06-20

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const AGE_COL = "Age (months)";
const P3_COL = "P3";
const P10_COL = "P10";
const P25_COL = "P25";
const P50_COL = "P50";
const P75_COL = "P75";
const P90_COL = "P90";
const P97_COL = "P97";
const PATIENT_COL = "Patient Weight (kg)";
const Y_AXIS_LABEL = "Weight (kg)";

const PERCENTILE_COLS = [
  P3_COL,
  P10_COL,
  P25_COL,
  P50_COL,
  P75_COL,
  P90_COL,
  P97_COL,
] as const;

const Z_SCORES = [-1.88, -1.28, -0.67, 0, 0.67, 1.28, 1.88];
const BANDS: Array<{ loIdx: number; hiIdx: number; opacity: number }> = [
  { loIdx: 0, hiIdx: 1, opacity: 0.25 },
  { loIdx: 1, hiIdx: 2, opacity: 0.17 },
  { loIdx: 2, hiIdx: 4, opacity: 0.09 },
  { loIdx: 4, hiIdx: 5, opacity: 0.17 },
  { loIdx: 5, hiIdx: 6, opacity: 0.25 },
];
const Y_TOP_PAD_SHARE = 0.08;

// Data: WHO Boys weight-for-age reference curves (0–36 months) + well-child patient visits
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

const DATA: Array<{
  [AGE_COL]: number;
  [P3_COL]: number;
  [P10_COL]: number;
  [P25_COL]: number;
  [P50_COL]: number;
  [P75_COL]: number;
  [P90_COL]: number;
  [P97_COL]: number;
  [PATIENT_COL]: number | null;
}> = [];

for (let ageM = 0; ageM <= 36; ageM += 1) {
  const med = 16 - 12.7 * Math.exp(-0.057 * ageM);
  const cv = 0.128 - (0.013 * ageM) / 36;
  DATA.push({
    [AGE_COL]: ageM,
    [P3_COL]: Number((med * (1 + Z_SCORES[0] * cv)).toFixed(2)),
    [P10_COL]: Number((med * (1 + Z_SCORES[1] * cv)).toFixed(2)),
    [P25_COL]: Number((med * (1 + Z_SCORES[2] * cv)).toFixed(2)),
    [P50_COL]: Number((med * (1 + Z_SCORES[3] * cv)).toFixed(2)),
    [P75_COL]: Number((med * (1 + Z_SCORES[4] * cv)).toFixed(2)),
    [P90_COL]: Number((med * (1 + Z_SCORES[5] * cv)).toFixed(2)),
    [P97_COL]: Number((med * (1 + Z_SCORES[6] * cv)).toFixed(2)),
    [PATIENT_COL]:
      ageM in PATIENT_VISITS ? PATIENT_VISITS[ageM] : null,
  });
}

// Sort by age before drawing lines
const sortedData = [...DATA].sort((a, b) => a[AGE_COL] - b[AGE_COL]);
const ages = sortedData.map((d) => d[AGE_COL]);
const X_MIN = Math.min(...ages);
const X_MAX = Math.max(...ages);

const allRefValues = sortedData.flatMap((d) =>
  PERCENTILE_COLS.map((col) => d[col]),
);
const patientPoints = sortedData
  .filter((d) => d[PATIENT_COL] !== null)
  .map((d) => ({ age: d[AGE_COL], weight: d[PATIENT_COL]! }));

const maxRefVal = Math.max(
  ...allRefValues,
  ...patientPoints.map((p) => p.weight),
);
const Y_MIN = 0;
const Y_MAX = Math.ceil((maxRefVal * (1 + Y_TOP_PAD_SHARE)) / 2) * 2;

const BAND_COLOR = t.palette[2];
const PATIENT_COLOR = t.palette[0];

function GrowthChartLayer() {
  const xScale = useXScale("age") as (v: number) => number;
  const yScale = useYScale("weight") as (v: number) => number;
  if (!xScale || !yScale) return null;

  const rightEdgeX = xScale(X_MAX) + 12;
  const patientPath = patientPoints
    .map(
      (pt, i) =>
        `${i === 0 ? "M" : "L"} ${xScale(pt.age).toFixed(1)} ${yScale(
          pt.weight,
        ).toFixed(1)}`,
    )
    .join(" ");

  return (
    <g>
      {/* Filled percentile bands (P3→P97) */}
      {BANDS.map((band, idx) => {
        const loCol = PERCENTILE_COLS[band.loIdx];
        const hiCol = PERCENTILE_COLS[band.hiIdx];
        let d = `M ${xScale(sortedData[0][AGE_COL]).toFixed(1)} ${yScale(
          sortedData[0][hiCol],
        ).toFixed(1)}`;
        for (let i = 1; i < sortedData.length; i += 1) {
          d += ` L ${xScale(sortedData[i][AGE_COL]).toFixed(1)} ${yScale(
            sortedData[i][hiCol],
          ).toFixed(1)}`;
        }
        for (let i = sortedData.length - 1; i >= 0; i -= 1) {
          d += ` L ${xScale(sortedData[i][AGE_COL]).toFixed(1)} ${yScale(
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

      {/* Percentile reference curves */}
      {PERCENTILE_COLS.map((col) => {
        const isMedian = col === P50_COL;
        const pathD = sortedData
          .map(
            (row, i) =>
              `${i === 0 ? "M" : "L"} ${xScale(row[AGE_COL]).toFixed(
                1,
              )} ${yScale(row[col]).toFixed(1)}`,
          )
          .join(" ");

        return (
          <path
            key={`line-${col}`}
            d={pathD}
            fill="none"
            stroke={BAND_COLOR}
            strokeWidth={isMedian ? 2.8 : 1.3}
            strokeOpacity={isMedian ? 0.94 : 0.58}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}

      {/* Patient trajectory line and markers */}
      <path
        d={patientPath}
        stroke={PATIENT_COLOR}
        strokeWidth={3.2}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {patientPoints.map((pt) => (
        <circle
          key={`pt-${pt.age}`}
          cx={xScale(pt.age)}
          cy={yScale(pt.weight)}
          r={6.2}
          fill={PATIENT_COLOR}
          stroke={t.pageBg}
          strokeWidth={2}
        />
      ))}

      {/* Right-margin percentile labels (P3–P97) */}
      {PERCENTILE_COLS.map((col) => {
        const isMedian = col === P50_COL;
        const lastRow = sortedData[sortedData.length - 1];
        const yPx = yScale(lastRow[col]);

        return (
          <text
            key={`lbl-${col}`}
            x={rightEdgeX}
            y={yPx}
            fontSize={isMedian ? 16 : 14}
            fontWeight={isMedian ? 700 : 600}
            fontFamily={t.mono}
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

const anchorSeries = [
  {
    type: "line" as const,
    id: "_anchor",
    xAxisId: "age",
    yAxisId: "weight",
    data: ages.map(() => null),
    color: "transparent",
    showMark: false,
  },
];

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
        fontFamily: t.sans,
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
            Boys Weight-for-Age · line-growth-percentile · javascript · muix ·
            anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: t.mono,
            }}
          >
            WHO reference percentiles ({P3_COL}–{P97_COL}, {X_MIN}–{X_MAX} mo) ·{" "}
            {patientPoints.length} well-child visits ({firstVisit.weight.toFixed(2)}{" "}
            kg at birth → {lastVisit.weight.toFixed(2)} kg at {lastVisit.age} mo)
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
            <span>{PATIENT_COL}</span>
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
            <span>Median ({P50_COL})</span>
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
              WHO bands ({P3_COL}–{P97_COL})
            </span>
          </div>
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={{ left: 20, right: 72, top: 20, bottom: 20 }}
        skipAnimation
        series={anchorSeries}
        xAxis={[
          {
            id: "age",
            data: ages,
            scaleType: "linear",
            min: X_MIN,
            max: X_MAX,
            height: 60,
            tickMinStep: 6,
            label: AGE_COL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
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
            tickMinStep: 2,
            label: Y_AXIS_LABEL,
            labelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: t.mono,
            },
            valueFormatter: (v: number) => String(v),
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal vertical />
        <GrowthChartLayer />
        <ChartsXAxis axisId="age" />
        <ChartsYAxis axisId="weight" />
      </ChartsContainer>
    </div>
  );
}
