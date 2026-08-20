//# anyplot-orientation: square
// anyplot.ai
// heatmap-loss-triangle: Actuarial Loss Development Triangle
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-20
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import {
  useXScale,
  useYScale,
  useZColorScale,
  useDrawingArea,
} from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// --- Data: cumulative paid-claims triangle, $000s (in-memory, deterministic) ----------
// Tiny fixed-seed LCG — no Math.random() in the browser render harness.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}
const random = lcg(42);

const ACCIDENT_YEARS = Array.from({ length: 10 }, (_, i) => 2015 + i);
const DEVELOPMENT_PERIODS = Array.from({ length: 10 }, (_, i) => i + 1);
const LATEST_EVALUATION_YEAR = 2024;

// Age-to-age development factors, period p -> p+1 (classic chain-ladder decay).
const DEV_FACTORS = [1.45, 1.2, 1.12, 1.07, 1.045, 1.028, 1.017, 1.01, 1.005];

// Period-1 base losses grow with accident-year exposure plus mild noise.
const basePeriod1 = ACCIDENT_YEARS.map((year, i) =>
  Math.round(820 + i * 35 + (random() - 0.5) * 60),
);

// Full cumulative grid: same development factors drive both the observed
// history and the chain-ladder projection of the still-open accident years.
const cumulativeByYear = basePeriod1.map((base) => {
  const row = [base];
  for (let p = 1; p < DEVELOPMENT_PERIODS.length; p += 1) {
    row.push(row[p - 1] * DEV_FACTORS[p - 1]);
  }
  return row.map((value) => Math.round(value));
});

// Accident year `i` rows down from 2015 has (10 - i) periods observed by the
// latest evaluation date, so a cell is actual when row-index + development
// period <= 10 — the anti-diagonal running from the top-right corner to the
// bottom-left corner. Everything past it is the chain-ladder projection.
const cells = [];
ACCIDENT_YEARS.forEach((year, i) => {
  DEVELOPMENT_PERIODS.forEach((period, j) => {
    cells.push({
      id: `${year}-${period}`,
      x: String(period),
      y: String(year),
      value: cumulativeByYear[i][j],
      isProjected: i + period > DEVELOPMENT_PERIODS.length,
    });
  });
});

const allValues = cells.map((cell) => cell.value);
const MIN_VALUE = Math.min(...allValues);
const MAX_VALUE = Math.max(...allValues);

// --- Colour: sequential Imprint colormap (imprint_seq) driven by the z-axis colorMap --
function hexToRgb(hex) {
  const int = parseInt(hex.slice(1), 16);
  return [(int >> 16) & 255, (int >> 8) & 255, int & 255];
}

function lerp(a, b, ratio) {
  return Math.round(a + (b - a) * ratio);
}

function imprintSeqInterpolator(stops) {
  const [low, high] = stops.map(hexToRgb);
  return (position) => {
    const ratio = Math.min(1, Math.max(0, position));
    const [r, g, b] = [0, 1, 2].map((channel) =>
      lerp(low[channel], high[channel], ratio),
    );
    return `rgb(${r}, ${g}, ${b})`;
  };
}

// Cell text must stay legible against that cell's own fill luminance regardless
// of the current site theme, so pick between the two fixed Imprint ink literals
// (light-mode ink / dark-mode ink) rather than the theme-dependent `t.ink`.
const CELL_TEXT_ON_LIGHT_FILL = "#1A1A17";
const CELL_TEXT_ON_DARK_FILL = "#F0EFE8";

function textColorFor(fill) {
  const [r, g, b] = fill.match(/[\d.]+/g).map(Number);
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 140 ? CELL_TEXT_ON_LIGHT_FILL : CELL_TEXT_ON_DARK_FILL;
}

const HATCH_ID = "loss-triangle-hatch";

// --- Cells (custom composition: MUI X band scales + z-axis colour scale) --------------
function TriangleCells() {
  const xScale = useXScale();
  const yScale = useYScale();
  const colorScale = useZColorScale();

  return (
    <g>
      {cells.map((cell) => {
        const x = xScale(cell.x) ?? 0;
        const y = yScale(cell.y) ?? 0;
        const width = xScale.bandwidth();
        const height = yScale.bandwidth();
        const fill = colorScale(cell.value);
        const textFill = textColorFor(fill);
        return (
          <g key={cell.id}>
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              fill={fill}
              rx={4}
              stroke={cell.isProjected ? t.inkSoft : t.pageBg}
              strokeWidth={cell.isProjected ? 1.5 : 2}
              strokeDasharray={cell.isProjected ? "4 3" : undefined}
            />
            {cell.isProjected && (
              <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill={`url(#${HATCH_ID})`}
                rx={4}
              />
            )}
            <ChartsText
              text={cell.value.toLocaleString("en-US")}
              x={x + width / 2}
              y={y + height / 2}
              style={{
                fontSize: 13,
                fill: textFill,
                textAnchor: "middle",
                dominantBaseline: "central",
              }}
            />
          </g>
        );
      })}
    </g>
  );
}

// --- Age-to-age development factors, shown as a row below the triangle ----------------
function DevelopmentFactorRow() {
  const xScale = useXScale();
  const area = useDrawingArea();
  const rowY = area.top + area.height + 108;

  return (
    <g>
      <ChartsText
        text="Age-to-age factors"
        x={area.left - 12}
        y={rowY}
        style={{
          fontSize: 12,
          fill: t.inkSoft,
          textAnchor: "end",
          dominantBaseline: "central",
        }}
      />
      {DEV_FACTORS.map((factor, k) => {
        const period = k + 1;
        const boundaryX = (xScale(String(period)) ?? 0) + xScale.bandwidth();
        return (
          <ChartsText
            key={`factor-${period}`}
            text={`×${factor.toFixed(2)}`}
            x={boundaryX}
            y={rowY}
            style={{
              fontSize: 12,
              fill: t.inkSoft,
              textAnchor: "middle",
              dominantBaseline: "central",
            }}
          />
        );
      })}
    </g>
  );
}

// --- Actual vs. projected legend (manual swatches — not a data-series legend) ---------
const LEGEND_ITEMS = [
  { label: "Actual (observed)", hatched: false },
  { label: "Projected (IBNR estimate)", hatched: true },
];
const LEGEND_SWATCH = 18;
const LEGEND_GAP = 8;
const LEGEND_BLOCK_GAP = 40;
const LEGEND_CHAR_WIDTH = 7;

function LegendSwatches() {
  const blockWidths = LEGEND_ITEMS.map(
    (item) =>
      LEGEND_SWATCH + LEGEND_GAP + item.label.length * LEGEND_CHAR_WIDTH,
  );
  const totalWidth =
    blockWidths.reduce((sum, w) => sum + w, 0) +
    LEGEND_BLOCK_GAP * (LEGEND_ITEMS.length - 1);
  let cursorX = SIZE.width / 2 - totalWidth / 2;
  const y = 118;

  return (
    <g>
      {LEGEND_ITEMS.map((item, index) => {
        const swatchX = cursorX;
        cursorX += blockWidths[index] + LEGEND_BLOCK_GAP;
        return (
          <g key={item.label}>
            <rect
              x={swatchX}
              y={y - LEGEND_SWATCH / 2}
              width={LEGEND_SWATCH}
              height={LEGEND_SWATCH}
              rx={3}
              fill={t.seq[0]}
              stroke={item.hatched ? t.inkSoft : "none"}
              strokeDasharray={item.hatched ? "3 2" : undefined}
            />
            {item.hatched && (
              <rect
                x={swatchX}
                y={y - LEGEND_SWATCH / 2}
                width={LEGEND_SWATCH}
                height={LEGEND_SWATCH}
                rx={3}
                fill={`url(#${HATCH_ID})`}
              />
            )}
            <ChartsText
              text={item.label}
              x={swatchX + LEGEND_SWATCH + LEGEND_GAP}
              y={y}
              style={{
                fontSize: 13,
                fill: t.inkSoft,
                textAnchor: "start",
                dominantBaseline: "central",
              }}
            />
          </g>
        );
      })}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) ----------------------
const TITLE = "heatmap-loss-triangle · javascript · muix · anyplot.ai";
const MARGIN = { top: 190, right: 300, bottom: 200, left: 150 };
const LEGEND_CAPTION_X = SIZE.width - 26;
const LEGEND_CAPTION_Y = SIZE.height / 2;

export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      series={[]}
      margin={MARGIN}
      skipAnimation
      xAxis={[
        {
          scaleType: "band",
          data: DEVELOPMENT_PERIODS.map(String),
          categoryGapRatio: 0.06,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          scaleType: "band",
          data: ACCIDENT_YEARS.map(String),
          categoryGapRatio: 0.06,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      zAxis={[
        {
          colorMap: {
            type: "continuous",
            min: MIN_VALUE,
            max: MAX_VALUE,
            color: imprintSeqInterpolator(t.seq),
          },
        },
      ]}
    >
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
            strokeOpacity={0.22}
          />
        </pattern>
      </defs>
      <TriangleCells />
      <DevelopmentFactorRow />
      <ChartsXAxis />
      <ChartsYAxis />
      <g transform="translate(-28, 0)">
        <ContinuousColorLegend
          position={{ horizontal: "right", vertical: "middle" }}
          direction="column"
          length="50%"
          thickness={18}
          labelStyle={{ fontSize: 12, fill: t.inkSoft }}
        />
      </g>
      <ChartsText
        text="Cumulative paid claims ($000s)"
        x={LEGEND_CAPTION_X}
        y={LEGEND_CAPTION_Y}
        style={{
          fontSize: 12,
          fill: t.inkSoft,
          textAnchor: "middle",
          angle: -90,
        }}
      />
      <ChartsText
        text="Development Period (years since occurrence)"
        x={MARGIN.left + (SIZE.width - MARGIN.left - MARGIN.right) / 2}
        y={SIZE.height - MARGIN.bottom + 60}
        style={{
          fontSize: 14,
          fill: t.inkSoft,
          textAnchor: "middle",
        }}
      />
      <LegendSwatches />
      <ChartsText
        text={TITLE}
        x={SIZE.width / 2}
        y={50}
        style={{
          fontSize: 26,
          fontWeight: 600,
          fill: t.ink,
          textAnchor: "middle",
        }}
      />
      <ChartsText
        text={`Accident years ${ACCIDENT_YEARS[0]}–${ACCIDENT_YEARS[ACCIDENT_YEARS.length - 1]} · evaluated as of Dec ${LATEST_EVALUATION_YEAR}`}
        x={SIZE.width / 2}
        y={84}
        style={{
          fontSize: 15,
          fill: t.inkSoft,
          textAnchor: "middle",
        }}
      />
    </ChartContainer>
  );
}
