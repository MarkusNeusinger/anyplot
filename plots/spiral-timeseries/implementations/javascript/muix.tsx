// anyplot.ai
// spiral-timeseries: Spiral Time Series Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const CYCLE_PERIOD = "year"; // one revolution of the spiral is one calendar year, subdivided into months
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const INNER_RADIUS_SHARE = 0.14; // the first cycle starts this far out, as a share of the outer radius
const LABEL_RADIUS_SHARE = 1.1; // month labels sit just outside the outermost revolution
const FRAME_SHARE = 1.16; // the square drawing area spans the outer radius times this, each side
const MIN_STROKE = 2;
const STROKE_RAMP = 3.5; // extra stroke width at the highest value, a secondary value encoding
const COLORBAR_TICK_TARGET = 8;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const VALUE = "Daily mean temperature (°C)"; // role: value

// Data: replace this block with your own records, one object per row
// Five years of daily mean temperature at a mid-latitude station: a seasonal cycle of ±13 °C
// around 14 °C, a warming of 0.35 °C per year and day-to-day weather noise
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
  return Array.from({ length: 365 * 5 }, (_, day) => {
    const seasonal = -Math.cos((2 * Math.PI * (day % 365)) / 365) * 13;
    const trend = 0.35 * Math.floor(day / 365);
    const noise = (rand() - 0.5) * 3.5;
    return { [DATE]: new Date(2020, 0, 1 + day), [VALUE]: Math.round((14 + seasonal + trend + noise) * 10) / 10 };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DATE] - b[DATE]);
const values = rows.map((d) => d[VALUE]);
const vMin = Math.min(...values);
const vMax = Math.max(...values);
const firstYear = rows[0][DATE].getFullYear();
const years = [...new Set(rows.map((d) => d[DATE].getFullYear()))];
const cycleCount = rows[rows.length - 1][DATE].getFullYear() - firstYear + 1;
const gap = (1 - INNER_RADIUS_SHARE) / cycleCount;

// Archimedean spiral: elapsed cycles = whole years since the first plus the share of the
// current year, so the same date of every year sits at the same angle, clockwise from the top
const points = rows.map((d) => {
  const year = d[DATE].getFullYear();
  const yearStart = new Date(year, 0, 1);
  const share = (d[DATE] - yearStart) / (new Date(year + 1, 0, 1) - yearStart);
  const radius = INNER_RADIUS_SHARE + gap * (year - firstYear + share);
  const angle = Math.PI / 2 - 2 * Math.PI * share;
  return { x: radius * Math.cos(angle), y: radius * Math.sin(angle), value: d[VALUE] };
});
const seqRgb = t.seq.map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
const segments = points.slice(1).map((b, i) => {
  const a = points[i];
  const v = ((a.value + b.value) / 2 - vMin) / (vMax - vMin);
  return {
    a,
    b,
    width: MIN_STROKE + v * STROKE_RAMP,
    color: `rgb(${seqRgb[0].map((c, j) => Math.round(c + (seqRgb[1][j] - c) * v)).join(",")})`,
  };
});

// Month spokes at each month's start in the first cycle's calendar, labels at the month's middle
const refStart = new Date(firstYear, 0, 1);
const refLength = new Date(firstYear + 1, 0, 1) - refStart;
const monthShares = [...MONTH_NAMES.map((_, m) => (new Date(firstYear, m, 1) - refStart) / refLength), 1];
const months = MONTH_NAMES.map((name, m) => ({
  name,
  spoke: Math.PI / 2 - 2 * Math.PI * monthShares[m],
  middle: Math.PI / 2 - Math.PI * (monthShares[m] + monthShares[m + 1]),
}));
const cycleStarts = years.map((year) => ({
  id: `cycle-${year}`,
  x: 0,
  y: INNER_RADIUS_SHARE + gap * (year - firstYear),
  year,
}));

const rawStep = (vMax - vMin) / COLORBAR_TICK_TARGET;
const stepMagnitude = 10 ** Math.floor(Math.log10(rawStep));
const valueStep = [1, 2, 5, 10].map((m) => m * stepMagnitude).find((s) => s >= rawStep);
const valueTicks = Array.from(
  { length: Math.floor(vMax / valueStep) - Math.ceil(vMin / valueStep) + 1 },
  (_, i) => (Math.ceil(vMin / valueStep) + i) * valueStep,
);

const firstDateText = rows[0][DATE].toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
const lastDateText = rows[rows.length - 1][DATE].toLocaleDateString("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
});
const TITLE = "spiral-timeseries · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length.toLocaleString("en-US")} daily values, ${firstDateText} to ${lastDateText} · one revolution per ${CYCLE_PERIOD}, earliest at the centre`;
const HEADER_H = 84;
const LEGEND_W = 150;
const BASE_MARGIN = 40;
const BAR_W = 22;

function SpiralLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const cx = xScale(0);
  const cy = yScale(0);
  const unit = xScale(1) - cx;
  return (
    <g>
      {months.map((m) => (
        <line
          key={`spoke-${m.name}`}
          x1={cx + unit * INNER_RADIUS_SHARE * 0.6 * Math.cos(m.spoke)}
          y1={cy - unit * INNER_RADIUS_SHARE * 0.6 * Math.sin(m.spoke)}
          x2={cx + unit * 1.03 * Math.cos(m.spoke)}
          y2={cy - unit * 1.03 * Math.sin(m.spoke)}
          stroke={t.grid}
          strokeWidth={1.2}
        />
      ))}
      {months.map((m) => (
        <text
          key={`label-${m.name}`}
          x={cx + unit * LABEL_RADIUS_SHARE * Math.cos(m.middle)}
          y={cy - unit * LABEL_RADIUS_SHARE * Math.sin(m.middle)}
          textAnchor={Math.cos(m.middle) > 0.3 ? "start" : Math.cos(m.middle) < -0.3 ? "end" : "middle"}
          dominantBaseline="central"
          fontSize={15}
          fill={t.inkSoft}
        >
          {m.name}
        </text>
      ))}
      {segments.map((s, i) => (
        <line
          key={i}
          x1={xScale(s.a.x)}
          y1={yScale(s.a.y)}
          x2={xScale(s.b.x)}
          y2={yScale(s.b.y)}
          stroke={s.color}
          strokeWidth={s.width}
          strokeLinecap="round"
        />
      ))}
      {cycleStarts.map((c) => (
        <text
          key={c.id}
          x={xScale(c.x) - 10}
          y={yScale(c.y) - 16}
          textAnchor="end"
          dominantBaseline="central"
          fontSize={15}
          fontWeight={600}
          fill={t.ink}
        >
          {c.year}
        </text>
      ))}
    </g>
  );
}

function Colorbar() {
  const { width } = window.ANYPLOT_SIZE;
  const yScale = useYScale();
  const top = yScale(1);
  const bottom = yScale(-1);
  const x = width - LEGEND_W + 20;
  const yOf = (v) => bottom - ((v - vMin) / (vMax - vMin)) * (bottom - top);
  return (
    <g>
      <defs>
        <linearGradient id="spiralColorbar" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={x} y={top} width={BAR_W} height={bottom - top} fill="url(#spiralColorbar)" />
      {valueTicks.map((v) => (
        <g key={v}>
          <line x1={x + BAR_W} x2={x + BAR_W + 6} y1={yOf(v)} y2={yOf(v)} stroke={t.inkSoft} />
          <text x={x + BAR_W + 10} y={yOf(v)} dominantBaseline="middle" fontSize={14} fill={t.inkSoft}>
            {v.toString().replace("-", "−")}
          </text>
        </g>
      ))}
      <text
        x={x + BAR_W + 58}
        y={(top + bottom) / 2}
        textAnchor="middle"
        fontSize={16}
        fill={t.ink}
        transform={`rotate(90, ${x + BAR_W + 58}, ${(top + bottom) / 2})`}
      >
        {VALUE}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - HEADER_H;
  // A square drawing area keeps px per unit equal on both axes, so the spiral stays circular
  const side = chartH - 2 * BASE_MARGIN;
  const sideMargin = (width - LEGEND_W - side) / 2;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={chartH}
        margin={{ top: BASE_MARGIN, bottom: BASE_MARGIN, left: sideMargin, right: sideMargin + LEGEND_W }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "cycle-start",
            label: `Start of ${CYCLE_PERIOD}`,
            color: t.ink,
            markerSize: 6,
            data: cycleStarts,
            valueFormatter: (point) => `${point.year}`,
          },
        ]}
        xAxis={[{ scaleType: "linear", min: -FRAME_SHARE, max: FRAME_SHARE, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -FRAME_SHARE, max: FRAME_SHARE, position: "none" }]}
      >
        <SpiralLayer />
        <ScatterPlot />
        <Colorbar />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
    </div>
  );
}
