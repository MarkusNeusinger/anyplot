// anyplot.ai
// bullet-basic: Basic Bullet Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const BAND_OPACITY_DARK = 0.32; // ink share of the lowest (poorest) band
const BAND_OPACITY_LIGHT = 0.11; // ink share of the highest (best) band
const MEASURE_SHARE = 0.36; // measure bar thickness as a share of the band height
const TARGET_SHARE = 0.72; // target marker length as a share of the band height

// Columns: set these to your data's column names
const KPI = "KPI"; // role: label
const ACTUAL = "Actual"; // role: actual
const TARGET = "Target"; // role: target
const RANGES = ["Poor", "Satisfactory", "Good"]; // role: ranges (upper bound of each band, low to high)

// Data: replace this block with your own records, one object per row
// Quarterly KPI dashboard: actual performance against target, banded by
// poor / satisfactory / good qualitative ranges.
const data = [
  { [KPI]: "Quarterly Revenue ($M)", [ACTUAL]: 82, [TARGET]: 90, [RANGES[0]]: 50, [RANGES[1]]: 75, [RANGES[2]]: 100 },
  { [KPI]: "New Customers Acquired", [ACTUAL]: 145, [TARGET]: 130, [RANGES[0]]: 80, [RANGES[1]]: 120, [RANGES[2]]: 160 },
  { [KPI]: "Support SLA Compliance (%)", [ACTUAL]: 96, [TARGET]: 95, [RANGES[0]]: 85, [RANGES[1]]: 95, [RANGES[2]]: 100 },
  { [KPI]: "Project Milestones (%)", [ACTUAL]: 68, [TARGET]: 80, [RANGES[0]]: 40, [RANGES[1]]: 70, [RANGES[2]]: 100 },
];

// Plot: reads only data and the constants above
// Grayscale bands: ink at a falling opacity, darkest for the lowest range
const inkRgb = [1, 3, 5].map((i) => parseInt(t.ink.slice(i, i + 2), 16)).join(", ");
const bandColors = RANGES.map((_, i) => {
  const step = RANGES.length > 1 ? i / (RANGES.length - 1) : 0;
  return `rgba(${inkRgb}, ${BAND_OPACITY_DARK - step * (BAND_OPACITY_DARK - BAND_OPACITY_LIGHT)})`;
});

// Each bullet runs on its own linear scale from zero to its largest value
const rows = data.map((d) => ({
  label: d[KPI],
  actual: d[ACTUAL],
  target: d[TARGET],
  bandWidths: RANGES.map((col, i) => d[col] - (i > 0 ? d[RANGES[i - 1]] : 0)),
  max: Math.max(d[ACTUAL], d[TARGET], ...RANGES.map((col) => d[col])),
}));

const { width: W, height: H } = window.ANYPLOT_SIZE;
const TITLE_H = 78;
const KEY_H = 40;
const LABEL_W = 300;
const VALUE_W = 160;
const SIDE_PAD = 40;
const X_AXIS_H = 34;
const CHART_W = W - 2 * SIDE_PAD - LABEL_W - VALUE_W;
const ROW_H = Math.floor((H - TITLE_H - KEY_H - 24) / rows.length);

const TITLE = "bullet-basic · javascript · muix · anyplot.ai";
const subtitle = `${rows.length} metrics · bands ${RANGES.join(" / ")} · each bullet on its own scale from 0`;

function MeasureAndTarget({ actual, target }: { actual: number; target: number }) {
  const xScale = useXScale();
  const area = useDrawingArea();
  const mid = area.top + area.height / 2;
  const barH = area.height * MEASURE_SHARE;
  const targetH = area.height * TARGET_SHARE;
  return (
    <g>
      <rect x={xScale(0)} y={mid - barH / 2} width={xScale(actual) - xScale(0)} height={barH} fill={t.palette[0]} />
      <line x1={xScale(target)} x2={xScale(target)} y1={mid - targetH / 2} y2={mid + targetH / 2} stroke={t.ink} strokeWidth={4} />
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, display: "flex", flexDirection: "column", background: t.pageBg, padding: `0 ${SIDE_PAD}px`, boxSizing: "border-box" }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <div style={{ height: KEY_H, display: "flex", alignItems: "center", gap: 24, marginLeft: LABEL_W, fontSize: 15, color: t.inkSoft }}>
        {RANGES.map((name, i) => (
          <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 16, height: 16, background: bandColors[i], borderRadius: 2 }} />
            {name}
          </div>
        ))}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 26, height: 9, background: t.palette[0] }} />
          {ACTUAL}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 4, height: 18, background: t.ink }} />
          {TARGET}
        </div>
      </div>
      {rows.map((row) => (
        <div key={row.label} style={{ height: ROW_H, display: "flex", alignItems: "center" }}>
          <div style={{ width: LABEL_W, paddingRight: 20, boxSizing: "border-box", textAlign: "right", fontSize: 16, fontWeight: 500, color: t.ink, marginBottom: X_AXIS_H }}>
            {row.label}
          </div>
          <ChartsContainer
            width={CHART_W}
            height={ROW_H}
            skipAnimation
            margin={{ top: 14, bottom: 6, left: 12, right: 16 }}
            xAxis={[
              {
                min: 0,
                max: row.max,
                height: X_AXIS_H,
                tickNumber: 6,
                tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              },
            ]}
            yAxis={[{ scaleType: "band", data: [row.label], categoryGapRatio: 0, position: "none" }]}
            series={row.bandWidths.map((value, i) => ({
              type: "bar" as const,
              id: `band-${i}`,
              layout: "horizontal" as const,
              stack: "bands",
              data: [value],
              color: bandColors[i],
            }))}
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <BarPlot skipAnimation />
            <MeasureAndTarget actual={row.actual} target={row.target} />
            <ChartsXAxis />
          </ChartsContainer>
          <div style={{ width: VALUE_W, paddingLeft: 16, boxSizing: "border-box", marginBottom: X_AXIS_H }}>
            <span style={{ fontSize: 20, fontWeight: 600, color: t.ink }}>{row.actual}</span>
            <span style={{ fontSize: 15, color: t.inkSoft }}>{`  ${TARGET} ${row.target}`}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
