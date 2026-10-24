// anyplot.ai
// parallel-basic: Basic Parallel Coordinates Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-07-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const TITLE = "parallel-basic · javascript · muix · anyplot.ai";
const TITLE_H = 64;
const DIM_PAD_SHARE = 0.08;
const TARGET_TICK_DIVS = 3.5;

// Columns: set these to your data's column names
const ARCH = "Architecture"; // role: group
const DIMENSIONS = [
  "Batch size",
  "Hidden layers",
  "Dropout (%)",
  "Validation accuracy (%)",
  "Training time (min)",
]; // role: dimension

// Data: replace this block with your own records
const SEED = 20260724;
const DIM_BOUNDS: Array<[number, number]> = [
  [16, 256],
  [1, 8],
  [0, 50],
  [60, 99],
  [5, 180],
];
const ARCH_PROFILES: Array<{ name: string; count: number; centers: number[] }> = [
  { name: "CNN", count: 10, centers: [0.35, 0.5, 0.25, 0.65, 0.4] },
  { name: "RNN", count: 10, centers: [0.25, 0.35, 0.55, 0.35, 0.7] },
  { name: "Transformer", count: 10, centers: [0.75, 0.8, 0.35, 0.85, 0.85] },
];

let lcgState = SEED >>> 0;
const data: Array<Record<string, string | number>> = [];
for (const arch of ARCH_PROFILES) {
  for (let i = 0; i < arch.count; i += 1) {
    const row: Record<string, string | number> = { [ARCH]: arch.name };
    for (let d = 0; d < DIMENSIONS.length; d += 1) {
      lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
      const rand = lcgState / 4294967296;
      const jitter = (rand - 0.5) * 0.36;
      const fraction = Math.min(1, Math.max(0, arch.centers[d] + jitter));
      const [bMin, bMax] = DIM_BOUNDS[d];
      row[DIMENSIONS[d]] = Number((bMin + fraction * (bMax - bMin)).toFixed(2));
    }
    data.push(row);
  }
}

// Plot: reads only data and the constants above
const architectures: string[] = [];
for (const row of data) {
  const arch = String(row[ARCH]);
  if (!architectures.includes(arch)) architectures.push(arch);
}

const archColorMap: Record<string, string> = {};
for (let i = 0; i < architectures.length; i += 1) {
  archColorMap[architectures[i]] = t.palette[i];
}

interface DimensionConfig {
  col: string;
  min: number;
  max: number;
  ticks: number[];
  decimals: number;
}

const dimensions: DimensionConfig[] = DIMENSIONS.map((col) => {
  const vals = data.map((r) => Number(r[col]));
  const rawMin = Math.min(...vals);
  const rawMax = Math.max(...vals);
  const rawSpan = rawMax - rawMin;
  const pad = rawSpan * DIM_PAD_SHARE;
  const min = rawMin - pad;
  const max = rawMax + pad;
  const targetStep = (max - min) / TARGET_TICK_DIVS;
  const mag = 10 ** Math.floor(Math.log10(targetStep));
  const norm = targetStep / mag;
  const step = (norm <= 1.5 ? 1 : norm <= 3.5 ? 2 : norm <= 7.5 ? 5 : 10) * mag;
  const decimals = Math.max(0, -Math.floor(Math.log10(step) + 1e-9));
  const firstTick = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let v = firstTick; v <= max + step * 1e-6; v += step) {
    ticks.push(Number(v.toFixed(decimals)));
  }
  return {
    col,
    min,
    max,
    ticks,
    decimals,
  };
});

function ParallelCoordinatesOverlay() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();

  return (
    <g fontFamily={FONT}>
      <g fill="none" strokeWidth={1.8} strokeOpacity={0.58}>
        {data.map((row, i) => {
          const arch = String(row[ARCH]);
          const points = dimensions
            .map((dim, dIdx) => {
              const val = Number(row[dim.col]);
              const fraction = (val - dim.min) / (dim.max - dim.min);
              const x = xScale(dIdx);
              const y = top + height * (1 - fraction);
              return `${x},${y}`;
            })
            .join(" ");
          return <polyline key={i} points={points} stroke={archColorMap[arch]} />;
        })}
      </g>

      {dimensions.map((dim, i) => {
        const x = Number(xScale(i));
        return (
          <g key={dim.col}>
            <line x1={x} y1={top} x2={x} y2={top + height} stroke={t.inkSoft} strokeWidth={1.5} />
            {dim.ticks.map((tickVal) => {
              const f = (tickVal - dim.min) / (dim.max - dim.min);
              const y = top + height * (1 - f);
              const formatted = tickVal.toFixed(dim.decimals);
              return (
                <g key={tickVal}>
                  <line x1={x - 6} y1={y} x2={x + 6} y2={y} stroke={t.inkSoft} strokeWidth={1.5} />
                  <rect
                    x={x + 8}
                    y={y - 10}
                    width={formatted.length * 8.4 + 8}
                    height={20}
                    rx={3}
                    fill={t.pageBg}
                    fillOpacity={0.86}
                  />
                  <text x={x + 12} y={y} fontSize={14} fill={t.inkSoft} dominantBaseline="middle">
                    {formatted}
                  </text>
                </g>
              );
            })}
            <text x={x} y={top - 18} fontSize={15} fontWeight={600} fill={t.ink} textAnchor="middle">
              {dim.col}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const N = dimensions.length;

  return (
    <div
      style={{
        width: W,
        height: H,
        backgroundColor: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 90px",
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          {architectures.map((archName) => (
            <div key={archName} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: archColorMap[archName],
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: 15, color: t.ink }}>{archName}</span>
            </div>
          ))}
        </div>
      </div>
      <ChartsContainer
        width={W}
        height={H - TITLE_H}
        skipAnimation
        series={[]}
        margin={{ top: 56, right: 110, bottom: 36, left: 90 }}
        xAxis={[{ scaleType: "linear", min: 0, max: N - 1, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: 0, max: 1, position: "none" }]}
      >
        <ParallelCoordinatesOverlay />
      </ChartsContainer>
    </div>
  );
}
