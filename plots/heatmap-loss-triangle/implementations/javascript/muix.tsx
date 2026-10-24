// anyplot.ai
// heatmap-loss-triangle: Actuarial Loss Development Triangle
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-20
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// Constants
const ACCIDENT_YEAR_COL = "accident_year";
const DEV_PERIOD_COL = "development_period";
const CUMULATIVE_COL = "cumulative_amount";
const IS_PROJECTED_COL = "is_projected";
const DEV_FACTOR_COL = "development_factor";

const CELL_TEXT_ON_LIGHT_FILL = "#1A1A17";
const CELL_TEXT_ON_DARK_FILL = "#FAF8F1";
const HATCH_ID = "loss-triangle-hatch";
const GRAD_ID = "loss-triangle-seq-grad";
const COLORBAR_TICKS = [0, 0.25, 0.5, 0.75, 1];

// Data
const SEED_YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
const SEED_FACTORS = [1.45, 1.2, 1.12, 1.07, 1.045, 1.028, 1.017, 1.01, 1.005, 1.0];

type LossTriangleRow = {
  [ACCIDENT_YEAR_COL]: number;
  [DEV_PERIOD_COL]: number;
  [CUMULATIVE_COL]: number;
  [IS_PROJECTED_COL]: number;
  [DEV_FACTOR_COL]: number;
};

const DATA: LossTriangleRow[] = [];
let lcgState = 42;
const nPeriods = SEED_FACTORS.length;

for (let i = 0; i < SEED_YEARS.length; i++) {
  lcgState = (lcgState * 1103515245 + 12345) & 0x7fffffff;
  const rand = lcgState / 0x7fffffff;
  const baseLoss = Math.round(820 + i * 35 + (rand - 0.5) * 60);
  let cumulative = baseLoss;

  for (let j = 0; j < nPeriods; j++) {
    const period = j + 1;
    if (j > 0) {
      cumulative = cumulative * SEED_FACTORS[j - 1];
    }
    DATA.push({
      [ACCIDENT_YEAR_COL]: SEED_YEARS[i],
      [DEV_PERIOD_COL]: period,
      [CUMULATIVE_COL]: Math.round(cumulative),
      [IS_PROJECTED_COL]: i + period > nPeriods ? 1 : 0,
      [DEV_FACTOR_COL]: SEED_FACTORS[j],
    });
  }
}

const accidentYearNums = Array.from(
  new Set(DATA.map((r) => r[ACCIDENT_YEAR_COL])),
).sort((a, b) => a - b);
const devPeriodNums = Array.from(
  new Set(DATA.map((r) => r[DEV_PERIOD_COL])),
).sort((a, b) => a - b);

const accidentYearLabels = accidentYearNums.map(String);
const devPeriodLabels = devPeriodNums.map(String);

const factorByPeriod = new Map<number, number>();
for (const row of DATA) {
  const p = row[DEV_PERIOD_COL];
  if (!factorByPeriod.has(p) && p < devPeriodNums.length) {
    factorByPeriod.set(p, row[DEV_FACTOR_COL]);
  }
}

const allAmounts = DATA.map((r) => r[CUMULATIVE_COL]);
const minVal = Math.min(...allAmounts);
const maxVal = Math.max(...allAmounts);
const valSpan = Math.max(1, maxVal - minVal);

const seqLowNum = parseInt(t.seq[0].slice(1), 16);
const seqHighNum = parseInt(t.seq[1].slice(1), 16);
const lowR = (seqLowNum >> 16) & 255;
const lowG = (seqLowNum >> 8) & 255;
const lowB = seqLowNum & 255;
const highR = (seqHighNum >> 16) & 255;
const highG = (seqHighNum >> 8) & 255;
const highB = seqHighNum & 255;

const cells = DATA.map((row) => {
  const val = row[CUMULATIVE_COL];
  const ratio = Math.min(1, Math.max(0, (val - minVal) / valSpan));
  const r = Math.round(lowR + (highR - lowR) * ratio);
  const g = Math.round(lowG + (highG - lowG) * ratio);
  const b = Math.round(lowB + (highB - lowB) * ratio);
  const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  return {
    id: `${row[ACCIDENT_YEAR_COL]}-${row[DEV_PERIOD_COL]}`,
    yearKey: String(row[ACCIDENT_YEAR_COL]),
    periodKey: String(row[DEV_PERIOD_COL]),
    yearIdx: accidentYearNums.indexOf(row[ACCIDENT_YEAR_COL]),
    periodIdx: devPeriodNums.indexOf(row[DEV_PERIOD_COL]),
    value: val,
    isProjected: row[IS_PROJECTED_COL] === 1,
    fill: `rgb(${r}, ${g}, ${b})`,
    textFill: lum > 0.54 ? CELL_TEXT_ON_LIGHT_FILL : CELL_TEXT_ON_DARK_FILL,
  };
});

const latestYear = accidentYearNums[accidentYearNums.length - 1];
let totalIbnr = 0;
for (const year of accidentYearNums) {
  const yearRows = DATA.filter((r) => r[ACCIDENT_YEAR_COL] === year);
  const observedRows = yearRows.filter((r) => r[IS_PROJECTED_COL] === 0);
  const latestObserved =
    observedRows.length > 0
      ? observedRows[observedRows.length - 1][CUMULATIVE_COL]
      : 0;
  const ultimate =
    yearRows.length > 0 ? yearRows[yearRows.length - 1][CUMULATIVE_COL] : 0;
  totalIbnr += Math.max(0, ultimate - latestObserved);
}

const TITLE = "heatmap-loss-triangle · javascript · muix · anyplot.ai";
const SUBTITLE = `Accident years ${accidentYearNums[0]}–${latestYear} ($000s, Dec ${latestYear} diagonal) · Total projected IBNR reserve $${totalIbnr.toLocaleString("en-US")}k`;

function LossTriangleLayer() {
  const area = useDrawingArea();
  const xScale = useXScale("dev-period") as any;
  const yScale = useYScale("accident-year") as any;
  if (!xScale || !yScale || !xScale.bandwidth || !yScale.bandwidth) return null;

  const bw = xScale.bandwidth();
  const bh = yScale.bandwidth();
  const stepX =
    devPeriodLabels.length > 1
      ? (xScale(devPeriodLabels[1]) ?? 0) - (xScale(devPeriodLabels[0]) ?? 0)
      : bw;
  const stepY =
    accidentYearLabels.length > 1
      ? (yScale(accidentYearLabels[1]) ?? 0) - (yScale(accidentYearLabels[0]) ?? 0)
      : bh;

  const staircasePts: string[] = [];
  for (let i = 1; i < accidentYearLabels.length; i++) {
    const obsCount = devPeriodLabels.length - i;
    const xRight = (xScale(devPeriodLabels[obsCount - 1]) ?? 0) + bw + (stepX - bw) / 2;
    const yTop = (yScale(accidentYearLabels[i]) ?? 0) - (stepY - bh) / 2;
    const yBot = (yScale(accidentYearLabels[i]) ?? 0) + bh + (stepY - bh) / 2;
    if (i === 1) {
      const xFarRight = (xScale(devPeriodLabels[devPeriodLabels.length - 1]) ?? 0) + bw;
      staircasePts.push(`M ${xFarRight} ${yTop}`);
    }
    staircasePts.push(`L ${xRight} ${yTop}`);
    staircasePts.push(`L ${xRight} ${yBot}`);
  }
  const staircasePath = staircasePts.join(" ");

  const factorRowY = area.top + area.height + 92;
  const barX = area.left + area.width + 28;
  const barW = 18;
  const barTop = area.top + area.height * 0.12;
  const barH = area.height * 0.78;

  return (
    <g>
      <defs>
        <pattern
          id={HATCH_ID}
          width={8}
          height={8}
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <line
            x1={0}
            y1={0}
            x2={0}
            y2={8}
            stroke={t.ink}
            strokeWidth={2}
            strokeOpacity={0.24}
          />
        </pattern>
        <linearGradient id={GRAD_ID} x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>

      <text
        x={SIZE.width / 2}
        y={42}
        textAnchor="middle"
        fontSize={22}
        fontWeight="600"
        fill={t.ink}
      >
        {TITLE}
      </text>
      <text
        x={SIZE.width / 2}
        y={70}
        textAnchor="middle"
        fontSize={15}
        fill={t.inkSoft}
      >
        {SUBTITLE}
      </text>

      {/* Legend swatches: Actual vs Projected */}
      <g transform={`translate(${SIZE.width / 2 - 225}, 96)`}>
        <rect
          x={0}
          y={0}
          width={20}
          height={20}
          rx={3}
          fill={t.seq[0]}
          stroke={t.pageBg}
          strokeWidth={1.5}
        />
        <text
          x={28}
          y={15}
          fontSize={14}
          fontWeight="600"
          fill={t.ink}
        >
          Actual (observed claims)
        </text>

        <rect
          x={235}
          y={0}
          width={20}
          height={20}
          rx={3}
          fill={t.seq[0]}
          stroke={t.inkSoft}
          strokeWidth={1.5}
          strokeDasharray="4 2"
        />
        <rect
          x={235}
          y={0}
          width={20}
          height={20}
          rx={3}
          fill={`url(#${HATCH_ID})`}
        />
        <text
          x={263}
          y={15}
          fontSize={14}
          fontWeight="600"
          fill={t.ink}
        >
          Projected (chain-ladder IBNR)
        </text>
      </g>

      {/* Triangle cells */}
      {cells.map((cell) => {
        const x = xScale(cell.periodKey) ?? 0;
        const y = yScale(cell.yearKey) ?? 0;
        return (
          <g key={cell.id}>
            <rect
              x={x}
              y={y}
              width={bw}
              height={bh}
              fill={cell.fill}
              rx={4}
              stroke={cell.isProjected ? t.inkSoft : t.pageBg}
              strokeWidth={cell.isProjected ? 1.5 : 2}
              strokeDasharray={cell.isProjected ? "4 3" : undefined}
            />
            {cell.isProjected && (
              <rect
                x={x}
                y={y}
                width={bw}
                height={bh}
                fill={`url(#${HATCH_ID})`}
                rx={4}
              />
            )}
            <text
              x={x + bw / 2}
              y={y + bh / 2}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={14}
              fontWeight="600"
              fill={cell.textFill}
            >
              {cell.value.toLocaleString("en-US")}
            </text>
          </g>
        );
      })}

      {/* Latest evaluation diagonal boundary */}
      <path
        d={staircasePath}
        fill="none"
        stroke={t.ink}
        strokeWidth={2.5}
      />

      {/* Age-to-age development factors row below the x-axis */}
      <text
        x={area.left}
        y={factorRowY}
        textAnchor="end"
        dominantBaseline="central"
        fontSize={14}
        fontWeight="600"
        fill={t.inkSoft}
      >
        Age-to-age factor
      </text>
      {devPeriodNums.slice(0, -1).map((period) => {
        const factor = factorByPeriod.get(period) ?? 1;
        const xLeft = (xScale(String(period)) ?? 0) + bw;
        const xRight = xScale(String(period + 1)) ?? xLeft;
        const boundaryX = (xLeft + xRight) / 2;
        return (
          <text
            key={`factor-${period}`}
            x={boundaryX}
            y={factorRowY}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={14}
            fontWeight="600"
            fill={t.inkSoft}
          >
            {`×${factor.toFixed(2)}`}
          </text>
        );
      })}

      {/* Sequential Colorbar */}
      <text
        x={barX}
        y={barTop - 30}
        textAnchor="start"
        fontSize={14}
        fontWeight="600"
        fill={t.ink}
      >
        Cumulative
      </text>
      <text
        x={barX}
        y={barTop - 12}
        textAnchor="start"
        fontSize={14}
        fill={t.inkSoft}
      >
        ($000s)
      </text>
      <rect
        x={barX}
        y={barTop}
        width={barW}
        height={barH}
        fill={`url(#${GRAD_ID})`}
        stroke={t.grid}
        strokeWidth={1}
        rx={3}
      />
      {COLORBAR_TICKS.map((frac) => {
        const val = Math.round(minVal + frac * valSpan);
        const ty = barTop + barH * (1 - frac);
        return (
          <g key={frac}>
            <line
              x1={barX + barW}
              y1={ty}
              x2={barX + barW + 6}
              y2={ty}
              stroke={t.inkSoft}
              strokeWidth={1}
            />
            <text
              x={barX + barW + 10}
              y={ty + 5}
              fontSize={14}
              fill={t.inkSoft}
            >
              {val.toLocaleString("en-US")}
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
      width={SIZE.width}
      height={SIZE.height}
      series={[]}
      margin={{ top: 138, right: 132, bottom: 64, left: 74 }}
      skipAnimation
      xAxis={[
        {
          id: "dev-period",
          scaleType: "band",
          data: devPeriodLabels,
          categoryGapRatio: 0.06,
          height: 58,
          label: "Development Period (years since occurrence)",
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontWeight: 600 },
          labelStyle: { fontSize: 15, fill: t.ink },
        },
      ]}
      yAxis={[
        {
          id: "accident-year",
          scaleType: "band",
          data: accidentYearLabels,
          categoryGapRatio: 0.06,
          width: 82,
          label: "Accident Year",
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontWeight: 600 },
          labelStyle: { fontSize: 15, fill: t.ink },
        },
      ]}
    >
      <LossTriangleLayer />
      <ChartsXAxis axisId="dev-period" />
      <ChartsYAxis axisId="accident-year" />
    </ChartsContainer>
  );
}
