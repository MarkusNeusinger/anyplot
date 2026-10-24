// anyplot.ai
// heatmap-loss-triangle: Actuarial Loss Development Triangle
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 0/100 | Updated: 2026-10-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "heatmap-loss-triangle · javascript · muix · anyplot.ai";
const CELL_TEXT_ON_LIGHT_FILL = "#1A1A17";
const CELL_TEXT_ON_DARK_FILL = "#FAF8F1";
const HATCH_ID = "loss-triangle-hatch";
const GRAD_ID = "loss-triangle-seq-grad";
const COLORBAR_TICKS = [0, 0.25, 0.5, 0.75, 1];

// Columns: set these to your data's column names
const ACCIDENT_YEAR = "Accident Year"; // role: accident_year
const DEV_PERIOD = "Development Period (years since occurrence)"; // role: development_period
const CUMULATIVE_CLAIMS = "Cumulative paid claims ($000s)"; // role: cumulative_amount
const IS_PROJECTED = "Projected"; // role: is_projected
const DEV_FACTOR = "Age-to-age factor"; // role: development_factor

// Data: replace this block with your own records
const SEED_YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
const SEED_FACTORS = [1.45, 1.2, 1.12, 1.07, 1.045, 1.028, 1.017, 1.01, 1.005, 1.0];

type LossTriangleRow = {
  [ACCIDENT_YEAR]: number;
  [DEV_PERIOD]: number;
  [CUMULATIVE_CLAIMS]: number;
  [IS_PROJECTED]: number;
  [DEV_FACTOR]: number;
};

const data: LossTriangleRow[] = [];
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
    data.push({
      [ACCIDENT_YEAR]: SEED_YEARS[i],
      [DEV_PERIOD]: period,
      [CUMULATIVE_CLAIMS]: Math.round(cumulative),
      [IS_PROJECTED]: i + period > nPeriods ? 1 : 0,
      [DEV_FACTOR]: SEED_FACTORS[j],
    });
  }
}

// Plot: reads only data and the constants above
const accidentYearNums = Array.from(
  new Set(data.map((r) => r[ACCIDENT_YEAR])),
).sort((a, b) => a - b);
const devPeriodNums = Array.from(
  new Set(data.map((r) => r[DEV_PERIOD])),
).sort((a, b) => a - b);

const accidentYearLabels = accidentYearNums.map(String);
const devPeriodLabels = devPeriodNums.map(String);

const factorByPeriod = new Map<number, number>();
for (const row of data) {
  const p = row[DEV_PERIOD];
  if (!factorByPeriod.has(p)) {
    factorByPeriod.set(p, row[DEV_FACTOR]);
  }
}

const maxObsPeriodIdxByYear = new Map<number, number>();
for (const year of accidentYearNums) {
  const obsPeriods = data
    .filter((r) => r[ACCIDENT_YEAR] === year && r[IS_PROJECTED] === 0)
    .map((r) => r[DEV_PERIOD]);
  const maxP = Math.max(...obsPeriods);
  maxObsPeriodIdxByYear.set(year, devPeriodNums.indexOf(maxP));
}

const allAmounts = data.map((r) => r[CUMULATIVE_CLAIMS]);
const minVal = Math.min(...allAmounts);
const maxVal = Math.max(...allAmounts);
const valSpan = maxVal - minVal;

const seqLowNum = parseInt(t.seq[0].slice(1), 16);
const seqHighNum = parseInt(t.seq[1].slice(1), 16);
const lowR = (seqLowNum >> 16) & 255;
const lowG = (seqLowNum >> 8) & 255;
const lowB = seqLowNum & 255;
const highR = (seqHighNum >> 16) & 255;
const highG = (seqHighNum >> 8) & 255;
const highB = seqHighNum & 255;

const cells = data.map((row) => {
  const val = row[CUMULATIVE_CLAIMS];
  const ratio = (val - minVal) / valSpan;
  const r = Math.round(lowR + (highR - lowR) * ratio);
  const g = Math.round(lowG + (highG - lowG) * ratio);
  const b = Math.round(lowB + (highB - lowB) * ratio);
  const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  return {
    id: `${row[ACCIDENT_YEAR]}-${row[DEV_PERIOD]}`,
    yearKey: String(row[ACCIDENT_YEAR]),
    periodKey: String(row[DEV_PERIOD]),
    value: val,
    isProjected: row[IS_PROJECTED] === 1,
    fill: `rgb(${r}, ${g}, ${b})`,
    textFill: lum > 0.54 ? CELL_TEXT_ON_LIGHT_FILL : CELL_TEXT_ON_DARK_FILL,
  };
});

const latestYear = accidentYearNums[accidentYearNums.length - 1];
let totalIbnr = 0;
for (const year of accidentYearNums) {
  const yearRows = data.filter((r) => r[ACCIDENT_YEAR] === year);
  const observedRows = yearRows.filter((r) => r[IS_PROJECTED] === 0);
  const latestObserved = observedRows[observedRows.length - 1][CUMULATIVE_CLAIMS];
  const ultimate = yearRows[yearRows.length - 1][CUMULATIVE_CLAIMS];
  totalIbnr += ultimate - latestObserved;
}

const unitMatch = CUMULATIVE_CLAIMS.match(/\(([^)]+)\)/);
const claimsUnit = unitMatch ? unitMatch[1] : "";
const claimsName = CUMULATIVE_CLAIMS.replace(/\s*\([^)]*\)/, "");
const subtitle = `${ACCIDENT_YEAR}s ${accidentYearNums[0]}–${latestYear} · ${CUMULATIVE_CLAIMS} · Total projected IBNR reserve: ${totalIbnr.toLocaleString("en-US")} (${claimsUnit})`;

function LossTriangleLayer() {
  const area = useDrawingArea();
  const xScale = useXScale("dev-period") as unknown as ((v: string) => number) & { bandwidth: () => number };
  const yScale = useYScale("accident-year") as unknown as ((v: string) => number) & { bandwidth: () => number };

  const bw = xScale.bandwidth();
  const bh = yScale.bandwidth();
  const stepX = xScale(devPeriodLabels[1]) - xScale(devPeriodLabels[0]);
  const stepY = yScale(accidentYearLabels[1]) - yScale(accidentYearLabels[0]);

  const staircasePts: string[] = [];
  let prevXRight = xScale(devPeriodLabels[devPeriodLabels.length - 1]) + bw;
  for (let i = 0; i < accidentYearNums.length; i++) {
    const year = accidentYearNums[i];
    const maxObsIdx = maxObsPeriodIdxByYear.get(year)!;
    if (maxObsIdx < devPeriodLabels.length - 1) {
      const xRight = xScale(devPeriodLabels[maxObsIdx]) + bw + (stepX - bw) / 2;
      const yTop = yScale(accidentYearLabels[i]) - (stepY - bh) / 2;
      const yBot = yScale(accidentYearLabels[i]) + bh + (stepY - bh) / 2;
      if (staircasePts.length === 0) {
        staircasePts.push(`M ${prevXRight} ${yTop}`);
      }
      staircasePts.push(`L ${xRight} ${yTop}`);
      staircasePts.push(`L ${xRight} ${yBot}`);
      prevXRight = xRight;
    } else {
      prevXRight = xScale(devPeriodLabels[maxObsIdx]) + bw;
    }
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
        {subtitle}
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
        const x = xScale(cell.periodKey);
        const y = yScale(cell.yearKey);
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
        {DEV_FACTOR}
      </text>
      {devPeriodNums.slice(0, -1).map((period, k) => {
        const nextPeriod = devPeriodNums[k + 1];
        const factor = factorByPeriod.get(period)!;
        const xLeft = xScale(String(period)) + bw;
        const xRight = xScale(String(nextPeriod));
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
        {claimsName}
      </text>
      <text
        x={barX}
        y={barTop - 12}
        textAnchor="start"
        fontSize={14}
        fill={t.inkSoft}
      >
        {`(${claimsUnit})`}
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
          label: DEV_PERIOD,
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
          label: ACCIDENT_YEAR,
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
