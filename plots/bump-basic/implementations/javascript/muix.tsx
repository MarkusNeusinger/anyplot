// anyplot.ai
// bump-basic: Basic Bump Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const RANK_PAD_SHARE = 0.08; // rank-axis padding as a share of the rank span, keeps end marks inside

// Columns: set these to your data's column names
const LANGUAGE = "Language"; // role: entity
const YEAR = "Year"; // role: period
const RANK = "Popularity rank"; // role: rank

// Data: replace this block with your own records, one object per row
// Programming-language popularity rank by year, 2018-2025 (each year ranks 1..6).
const data = [
  { lang: "JavaScript", ranks: [1, 1, 1, 2, 2, 2, 2, 2] },
  { lang: "Python", ranks: [3, 2, 2, 1, 1, 1, 1, 1] },
  { lang: "Java", ranks: [2, 3, 4, 4, 5, 5, 6, 6] },
  { lang: "TypeScript", ranks: [6, 6, 5, 5, 4, 3, 3, 3] },
  { lang: "Go", ranks: [5, 5, 6, 6, 6, 6, 5, 4] },
  { lang: "Rust", ranks: [4, 4, 3, 3, 3, 4, 4, 5] },
].flatMap(({ lang, ranks }) =>
  ranks.map((rank, i) => ({ [LANGUAGE]: lang, [YEAR]: String(2018 + i), [RANK]: rank })),
);

// Plot: reads only data and the constants above
// Periods keep their order of appearance; entities are colored in order of first appearance
const periods = [...new Set(data.map((d) => d[YEAR]))];
const entities = [...new Set(data.map((d) => d[LANGUAGE]))];
const rankMap = new Map(data.map((d) => [`${d[LANGUAGE]}|${d[YEAR]}`, d[RANK]]));
const series = entities.map((entity, i) => ({
  id: `entity-${i}`,
  label: entity,
  color: t.palette[i],
  data: periods.map((p) => rankMap.get(`${entity}|${p}`) ?? null),
  showMark: true,
  shape: "circle" as const,
  curve: "monotoneX" as const,
}));

// Whole-number rank ticks from 1 to the lowest rank in the data
const maxRank = Math.max(...data.map((d) => d[RANK]));
const rankTicks = Array.from({ length: maxRank }, (_, i) => i + 1);
const rankPad = Math.max(1, maxRank - 1) * RANK_PAD_SHARE;

// Direct labels at each line's last ranked period
const endLabels = series.map((s) => {
  const lastIndex = s.data.findLastIndex((v) => v !== null);
  return { label: s.label, period: periods[lastIndex], rank: s.data[lastIndex] };
});

const TITLE = "Language Popularity Rankings · bump-basic · javascript · muix · anyplot.ai";
const subtitle = `${RANK} of ${entities.length} ${LANGUAGE.toLowerCase()}s per ${YEAR.toLowerCase()}, ${periods[0]}–${periods[periods.length - 1]} · 1 = top`;
const TITLE_H = 80;

function EndLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const half = xScale.bandwidth() / 2;
  return (
    <g>
      {endLabels.map((l) => (
        <text
          key={l.label}
          x={xScale(l.period) + half + 16}
          y={yScale(l.rank)}
          dominantBaseline="middle"
          fontSize={16}
          fontWeight={500}
          fill={t.ink}
        >
          {l.label}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", background: t.pageBg }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 16, bottom: 16, left: 24, right: 140 }}
        xAxis={[
          {
            scaleType: "band",
            data: periods,
            label: YEAR,
            height: 64,
            tickPlacement: "middle",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 1 - rankPad,
            max: maxRank + rankPad,
            reverse: true,
            tickInterval: rankTicks,
            valueFormatter: (v: number) => `#${v}`,
            label: RANK,
            width: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={series}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3.5 },
          "& .MuiLineChart-mark": { r: 6.5, strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <EndLabels />
      </LineChart>
    </div>
  );
}
