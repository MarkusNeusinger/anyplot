// anyplot.ai
// heatmap-cohort-retention: Cohort Retention Heatmap
// Library: muix 9.2.1 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-20
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const tok = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;

// Constants
const COHORT_COL = "cohort";
const COHORT_SIZE_COL = "cohort_size";
const PERIOD_COL = "period";
const RETENTION_COL = "retention_rate";

const SCALE_MAX = 100;
const COLORBAR_TICKS = [0, 25, 50, 75, 100];
const LIGHT_TEXT = "#FAF8F1";
const DARK_TEXT = "#1A1A17";

// Data
const COHORT_SEEDS = [
  { cohort: "Jan 2024", size: 4821 },
  { cohort: "Feb 2024", size: 3956 },
  { cohort: "Mar 2024", size: 5234 },
  { cohort: "Apr 2024", size: 4102 },
  { cohort: "May 2024", size: 6187 },
  { cohort: "Jun 2024", size: 5543 },
  { cohort: "Jul 2024", size: 4798 },
  { cohort: "Aug 2024", size: 5912 },
  { cohort: "Sep 2024", size: 4445 },
  { cohort: "Oct 2024", size: 3821 },
];

type RetentionRow = {
  [COHORT_COL]: string;
  [COHORT_SIZE_COL]: number;
  [PERIOD_COL]: number;
  [RETENTION_COL]: number;
};

const DATA: RetentionRow[] = [];
let lcg = 42 >>> 0;
const totalPeriods = COHORT_SEEDS.length;

for (let ci = 0; ci < COHORT_SEEDS.length; ci++) {
  const seed = COHORT_SEEDS[ci];
  const elapsedPeriods = totalPeriods - ci;
  for (let pi = 0; pi < elapsedPeriods; pi++) {
    let retention = SCALE_MAX;
    if (pi > 0) {
      lcg = (lcg * 1664525 + 1013904223) >>> 0;
      const noise = (lcg / 4294967296 - 0.5) * 10;
      const base = SCALE_MAX * Math.pow(0.8, pi) + 5 / (1 + 0.4 * pi);
      retention = Math.max(2, Math.min(97, Math.round(base + noise)));
    }
    DATA.push({
      [COHORT_COL]: seed.cohort,
      [COHORT_SIZE_COL]: seed.size,
      [PERIOD_COL]: pi,
      [RETENTION_COL]: retention,
    });
  }
}

const cohorts: string[] = [];
const cohortSizeByLabel = new Map<string, number>();
const periodSet = new Set<number>();

for (const row of DATA) {
  const c = row[COHORT_COL];
  if (!cohortSizeByLabel.has(c)) {
    cohorts.push(c);
    cohortSizeByLabel.set(c, row[COHORT_SIZE_COL]);
  }
  periodSet.add(row[PERIOD_COL]);
}

const periods = Array.from(periodSet)
  .sort((a, b) => a - b)
  .map((p) => String(p));

const seqStartHex = tok.seq[0].replace("#", "");
const seqEndHex = tok.seq[1].replace("#", "");
const seqStartNum = parseInt(seqStartHex, 16);
const seqEndNum = parseInt(seqEndHex, 16);
const r1 = (seqStartNum >> 16) & 255;
const g1 = (seqStartNum >> 8) & 255;
const b1 = seqStartNum & 255;
const r2 = (seqEndNum >> 16) & 255;
const g2 = (seqEndNum >> 8) & 255;
const b2 = seqEndNum & 255;

const cells = DATA.map((row) => {
  const val = row[RETENTION_COL];
  const ratio = Math.max(0, Math.min(1, val / SCALE_MAX));
  const r = Math.round(r1 + ratio * (r2 - r1));
  const g = Math.round(g1 + ratio * (g2 - g1));
  const b = Math.round(b1 + ratio * (b2 - b1));
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return {
    cohort: row[COHORT_COL],
    periodKey: String(row[PERIOD_COL]),
    val,
    fill: `rgb(${r},${g},${b})`,
    textFill: lum > 0.54 ? DARK_TEXT : LIGHT_TEXT,
  };
});

const period1Rows = DATA.filter((r) => r[PERIOD_COL] === 1);
const avgPeriod1 =
  period1Rows.reduce((acc, r) => acc + r[RETENTION_COL], 0) /
  Math.max(1, period1Rows.length);
const totalUsers = cohorts.reduce((acc, c) => acc + (cohortSizeByLabel.get(c) ?? 0), 0);

const TITLE = "heatmap-cohort-retention · javascript · muix · anyplot.ai";
const SUBTITLE = `${cohorts.length} monthly cohorts (${cohorts[0]}–${cohorts[cohorts.length - 1]}, n=${totalUsers.toLocaleString("en-US")}) · Month 1 mean retention ${avgPeriod1.toFixed(0)}%`;

function CohortRetentionLayer() {
  const { left, top, width, height } = useDrawingArea();
  const xScale = useXScale("periods") as any;
  const yScale = useYScale("cohorts") as any;
  if (!xScale || !yScale || !xScale.bandwidth || !yScale.bandwidth) return null;

  const bw = xScale.bandwidth();
  const bh = yScale.bandwidth();
  const barX = left + width + 22;
  const barW = 18;

  return (
    <g>
      <defs>
        <linearGradient id="cohortRetentionGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={tok.seq[0]} />
          <stop offset="100%" stopColor={tok.seq[1]} />
        </linearGradient>
      </defs>

      <text
        x={W / 2}
        y={36}
        textAnchor="middle"
        fontSize={22}
        fontWeight="600"
        fill={tok.ink}
      >
        {TITLE}
      </text>
      <text
        x={W / 2}
        y={62}
        textAnchor="middle"
        fontSize={15}
        fill={tok.inkSoft}
      >
        {SUBTITLE}
      </text>

      {cells.map((cell) => {
        const x0 = xScale(cell.periodKey);
        const y0 = yScale(cell.cohort);
        if (x0 === undefined || y0 === undefined) return null;
        return (
          <g key={`${cell.cohort}-${cell.periodKey}`}>
            <rect
              x={x0 + 1}
              y={y0 + 1}
              width={Math.max(0, bw - 2)}
              height={Math.max(0, bh - 2)}
              fill={cell.fill}
              rx={4}
            />
            <text
              x={x0 + bw / 2}
              y={y0 + bh / 2 + 5}
              textAnchor="middle"
              fontSize={14}
              fontWeight="600"
              fill={cell.textFill}
            >
              {cell.val}%
            </text>
          </g>
        );
      })}

      {cohorts.map((cohort) => {
        const y0 = yScale(cohort);
        if (y0 === undefined) return null;
        const mid = y0 + bh / 2;
        const size = cohortSizeByLabel.get(cohort) ?? 0;
        return (
          <g key={cohort}>
            <text
              x={left - 12}
              y={mid - 6}
              textAnchor="end"
              fontSize={14}
              fontWeight="600"
              fill={tok.ink}
            >
              {cohort}
            </text>
            <text
              x={left - 12}
              y={mid + 14}
              textAnchor="end"
              fontSize={14}
              fill={tok.inkSoft}
            >
              {`n=${size.toLocaleString("en-US")}`}
            </text>
          </g>
        );
      })}

      <text
        x={barX + barW / 2}
        y={top - 12}
        textAnchor="middle"
        fontSize={14}
        fontWeight="600"
        fill={tok.inkSoft}
      >
        Retention
      </text>
      <rect
        x={barX}
        y={top}
        width={barW}
        height={height}
        fill="url(#cohortRetentionGrad)"
        stroke={tok.grid}
        strokeWidth={1}
        rx={3}
      />
      {COLORBAR_TICKS.map((pct) => {
        const ty = top + height * (1 - pct / SCALE_MAX);
        return (
          <g key={pct}>
            <line
              x1={barX + barW}
              y1={ty}
              x2={barX + barW + 6}
              y2={ty}
              stroke={tok.inkSoft}
              strokeWidth={1}
            />
            <text
              x={barX + barW + 10}
              y={ty + 5}
              fontSize={14}
              fill={tok.inkSoft}
            >
              {pct}%
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  return (
    <ChartsContainer
      width={W}
      height={H}
      margin={{ left: 135, top: 92, right: 110, bottom: 24 }}
      xAxis={[
        {
          id: "periods",
          scaleType: "band",
          data: periods,
          categoryGapRatio: 0.04,
          height: 58,
          label: "Months Since Signup",
          valueFormatter: (v: string) => `Month ${v}`,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: tok.inkSoft },
          labelStyle: { fontSize: 15, fill: tok.ink },
        },
      ]}
      yAxis={[
        {
          id: "cohorts",
          scaleType: "band",
          data: cohorts,
          categoryGapRatio: 0.04,
          position: "none",
        },
      ]}
      series={[]}
      skipAnimation
    >
      <CohortRetentionLayer />
      <ChartsXAxis axisId="periods" />
    </ChartsContainer>
  );
}
